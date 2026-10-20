import logging
import os
import random
import time

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from web.models.collaboration import MultiAgentMessage

logger = logging.getLogger(__name__)

# 项目 .env 里实际可用的模型，作为兜底
FALLBACK_MODEL = os.getenv('DEFAULT_MODEL', 'deepseek-v4.1-flash')

# 自由讨论模式下，最多允许几轮全员发言，防止无限循环烧 token
MAX_FREE_ROUNDS = 3


def build_llm(participant, room):
    """按参与者配置构造 llm，未单独配置则回落到系统 API"""
    model = participant.model_name or room.model_name or FALLBACK_MODEL
    if participant.use_system_api or not participant.api_key:
        return ChatOpenAI(
            model=model,
            openai_api_key=os.getenv('API_KEY'),
            openai_api_base=os.getenv('API_BASE'),
            streaming=True,
        )
    return ChatOpenAI(
        model=model,
        openai_api_key=participant.api_key,
        openai_api_base=participant.api_base or os.getenv('API_BASE'),
        streaming=True,
    )


def get_turn_order(room):
    """按房间配置决定本轮发言顺序"""
    participants = list(room.participants.filter(enabled=True))
    if not participants:
        return []

    if room.turn_order == 'round_robin':
        # 记住上次发言位置，实现循环轮换
        last = MultiAgentMessage.objects.filter(
            room=room, speaker_type='agent'
        ).order_by('-turn_number', '-id').first()
        offset = 0
        if last and last.participant:
            ids = [p.id for p in participants]
            if last.participant.id in ids:
                offset = ids.index(last.participant.id) + 1
        return participants[offset:] + participants[:offset]

    if room.turn_order == 'random':
        random.shuffle(participants)
        return participants

    return participants


def build_history(participant, room, base_history, round_index=0):
    """按 flow_mode 决定某个 agent 能看到哪些历史消息。

    - moderated 主持人串联：看不到自己的发言（避免复读），并且只回看**上一轮**
      其他人的发言，形成"甲说完→乙点评甲→丙点评甲乙"的串联结构。
    - 其他模式：看完整上下文。
    """
    if room.flow_mode == 'moderated':
        # 取最近一轮里其他人的发言（自己的跳过）
        current_round = {m.turn_number for m in base_history if m.speaker_type == 'agent'}
        if round_index > 1 and current_round:
            last_round = max(current_round)
            relevant = [m for m in base_history if m.turn_number == last_round]
        else:
            relevant = base_history
    else:
        relevant = base_history

    chat_messages = []
    for msg in relevant:
        if msg.speaker_type == 'agent':
            if room.flow_mode == 'moderated' and msg.participant_id == participant.id:
                continue  # 主持人模式下不看自己说过的话
            chat_messages.append(
                HumanMessage(content=f'[{msg.speaker_name}] 说：{msg.content}')
            )
        else:
            chat_messages.append(HumanMessage(content=msg.content))
    return chat_messages


def stream_llm(llm, chat_messages):
    """流式调用模型，逐段 yield 增量文本。失败时用兜底模型重试一次。"""
    try:
        for chunk in llm.stream(chat_messages):
            text = getattr(chunk, 'content', '') or ''
            if text:
                yield text
        return
    except Exception as e:
        logger.warning('模型 %s 流式调用失败，尝试兜底模型：%s', llm.model_name, e)

    try:
        fallback_llm = ChatOpenAI(
            model=FALLBACK_MODEL,
            openai_api_key=os.getenv('API_KEY'),
            openai_api_base=os.getenv('API_BASE'),
            streaming=True,
        )
        for chunk in fallback_llm.stream(chat_messages):
            text = getattr(chunk, 'content', '') or ''
            if text:
                yield text
    except Exception as inner:
        logger.error('兜底模型同样失败：%s', inner)
        yield '（本次发言生成失败，请稍后重试）'


def speak(participant, room, history, prompt_suffix, turn_number, round_index=1):
    """让单个 agent 基于上下文发言。

    生成器：先 yield ('start', {...}) 表示该 agent 开始发言，
    再逐段 yield ('delta', 增量文本)，最后 yield ('done', 已落库的 Message)。
    发言内容为空时不会产出 'done'。
    """
    llm = build_llm(participant, room)

    system_content = participant.system_prompt or room.system_prompt or \
        '你正在参与一场多智能体讨论，请给出简洁、有见地的发言。'

    topic_prefix = f'讨论主题：{room.topic}\n' if room.topic else ''
    chat_messages = [SystemMessage(content=topic_prefix + system_content)]
    chat_messages.extend(build_history(participant, room, history, round_index))

    others = ', '.join(
        p.display_name for p in room.participants.filter(enabled=True)
        if p.id != participant.id
    )
    prompt = f'现在是 {participant.display_name} 的发言时间。'
    if others:
        prompt += f'其他参与者有：{others}。'
    prompt += prompt_suffix
    chat_messages.append(HumanMessage(content=prompt))

    yield ('start', {'speaker_name': participant.display_name, 'speaker_id': participant.id})

    parts = []
    for delta in stream_llm(llm, chat_messages):
        parts.append(delta)
        yield ('delta', delta)

    content = ''.join(parts).strip()
    if not content:
        return

    message = MultiAgentMessage.objects.create(
        room=room,
        participant=participant,
        speaker_type='agent',
        speaker_name=participant.display_name,
        content=content,
        turn_number=turn_number,
    )
    yield ('done', message)

def wants_to_continue(room, history):
    """自由讨论用：让第一个 agent 判断讨论是否值得继续一轮。

    判定失败时保守返回 False，避免每次都白跑一轮。
    """
    if not history:
        return False

    judge = history[-1]
    if judge.speaker_type != 'agent' or not judge.participant:
        return False

    participant = judge.participant
    recent = '\n'.join(
        f'{m.speaker_name}：{m.content[:200]}' for m in history[-6:]
    )
    topic = room.topic or '（无特定主题）'

    llm = build_llm(participant, room)
    chat_messages = [
        SystemMessage(content='你是讨论的观察者，只做判断，不参与讨论。'),
        HumanMessage(content=(
            f'讨论主题：{topic}\n\n'
            f'最近的讨论内容：\n{recent}\n\n'
            f'请判断：讨论是否还有新的见解可以补充，值得让所有人再发言一轮？\n'
            f'只回复「继续」或「结束」两个词之一，不要有其他内容。'
        )),
    ]

    try:
        answer = llm.invoke(chat_messages)
        text = (answer.content or '').strip()
    except Exception as e:
        logger.warning('自由讨论续轮判定失败：%s', e)
        return False

    return text.startswith('继续')


def run_round(room, user_input, turn_number):
    """按 flow_mode 跑一轮讨论，逐事件产出（生成器）。

    事件类型：
      ('start', {...}) 某 agent 开始发言
      ('delta', str)  该 agent 的增量文本
      ('done', Message) 该 agent 发言结束并已落库

    - round_robin 轮流发言：每人恰好一次，到此结束
    - moderated 主持人串联：每人一次，且看不到自己的历史发言，由主持人推进话题
    - free 自由讨论：先每人一轮，之后由 agent 自发决定是否继续接力（上限 MAX_FREE_ROUNDS 轮）
    """
    history = MultiAgentMessage.objects.filter(room=room).order_by('-id')[:40]
    history = list(reversed(history))

    flow_mode = room.flow_mode
    order = get_turn_order(room)
    if not order:
        return

    if flow_mode == 'moderated':
        suffix = (
            '你是本场讨论的主持人。请**先点名点评上一轮其他人的观点**（明确说谁的观点可取、谁需要补充），'
            '再抛出下一个值得讨论的问题，把话题往前推进一步。不要重复自己说过的话。'
        )
    elif flow_mode == 'free':
        suffix = '现在是自由讨论，请自由发表你的观点，也可以回应或反驳别人的看法。'
    else:
        suffix = '请回应刚才的发言，说出你的观点，不要重复别人说过的话。'

    max_rounds = MAX_FREE_ROUNDS if flow_mode == 'free' else 1

    for round_index in range(1, max_rounds + 1):
        # 第一轮固定全员发言；自由讨论的后续轮次由 agent 自愿决定是否继续
        if round_index > 1 and not wants_to_continue(room, history):
            yield ('notice', '智能体们认为讨论可以暂时收尾了')
            break

        for participant in order:
            last_message = None
            for event in speak(participant, room, history, suffix, turn_number, round_index):
                if event[0] == 'done':
                    last_message = event[1]
                yield event

            if last_message is None:
                continue

            history.append(last_message)

            if room.interval_seconds > 0:
                time.sleep(room.interval_seconds)
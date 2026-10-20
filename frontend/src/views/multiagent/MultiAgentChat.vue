<script setup>
import {computed, onMounted, onUnmounted, ref} from "vue";
import {useRoute, useRouter} from "vue-router";
import api from "@/js/http/api.js";
import CONFIG_API from "@/js/config/config.js";
import {useUserStore} from "@/stores/user.js";
import {fetchCharacters} from "@/js/api/character.js";

const route = useRoute()
const router = useRouter()
const user = useUserStore()

const room = ref(null)
const messages = ref([])
const characters = ref([])
const inputText = ref('')
const sending = ref(false)
const loading = ref(true)
const streamingMessage = ref(null)  // 正在流式接收的消息
const systemNotices = ref([])       // 系统提示（如讨论收尾）
const sendError = ref('')

const showSettings = ref(false)
const settings = ref({
    name: '', topic: '', system_prompt: '', model_name: 'deepseek-v4.1-flash',
    interval_seconds: 0, flow_mode: 'round_robin', turn_order: 'configured',
    participants: [],
})

const FLOW_MODES = [
    {value: 'round_robin', label: '轮流发言', hint: '每位参与者各发言一次，简洁一轮结束'},
    {value: 'moderated', label: '主持人串联', hint: '每人一次，由主持人点评并推进话题'},
    {value: 'free', label: '自由讨论', hint: '每人先发言一轮，若仍有新见解可自发继续（最多 3 轮）'},
]
const TURN_ORDERS = [
    {value: 'configured', label: '按配置顺序', hint: '每次都按设置里排列的顺序发言'},
    {value: 'round_robin', label: '循环轮换', hint: '上次最后发言的人，下次从他后面接着轮'},
    {value: 'random', label: '随机发言', hint: '每轮随机打乱发言顺序'},
]

/** 讨论流程说明，实时提示当前模式的区别 */
const flowHint = computed(() =>
    FLOW_MODES.find(m => m.value === settings.value.flow_mode)?.hint || ''
)
const turnHint = computed(() =>
    TURN_ORDERS.find(o => o.value === settings.value.turn_order)?.hint || ''
)

const groupedMessages = computed(() => messages.value)

/**
 * 清洗模型输出里的 Markdown 标记，只做「去掉符号、保留文字」。
 * 智能体回复是纯文本渲染，不解析 Markdown，所以星号等符号会原样显示很难看。
 */
function stripMarkdown(text) {
    if (!text) return ''
    return String(text)
        // 粗体/斜体：***x***、**x**、*x*、__x__、_x_
        .replace(/(\*\*\*|___)(.*?)\1/g, '$2')
        .replace(/(\*\*|__)(.*?)\1/g, '$2')
        .replace(/(\*|_)(?=\S)(.*?\S)\1/g, '$2')
        // 行内代码 `x` → x
        .replace(/`([^`]*)`/g, '$1')
        // 标题井号 # ## ###
        .replace(/^\s{0,3}#{1,6}\s+/gm, '')
        // 引用、列表符号
        .replace(/^\s{0,3}>\s?/gm, '')
        .replace(/^\s{0,3}[-*+]\s+/gm, '')
        // 链接 [文字](链接) → 文字
        .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
        // 残留的孤立星号
        .replace(/\*/g, '')
        .replace(/_{2,}/g, '')
}

/** 列表渲染用：清洗后的文本 */
const displayMessages = computed(() =>
    messages.value.map(m => ({...m, content: stripMarkdown(m.content)}))
)

async function loadRoom() {
    loading.value = true
    try {
        const res = await api.get(`/api/multi-agent/rooms/${route.params.room_id}/`)
        if (res.data.result === 'success') {
            room.value = res.data.room
            settings.value = {
                name: room.value.name,
                topic: room.value.topic,
                system_prompt: room.value.system_prompt,
                model_name: room.value.model_name,
                interval_seconds: room.value.interval_seconds,
                flow_mode: room.value.flow_mode,
                turn_order: room.value.turn_order,
                participants: room.value.participants.map(p => ({
                    character_id: p.character_id || '',
                    display_name: p.display_name,
                    model_name: p.model_name,
                    api_base: p.api_base,
                    use_system_api: p.use_system_api,
                    system_prompt: p.system_prompt,
                })),
            }
        } else {
            alert(res.data.result)
            router.push({name: 'multi-agent-index'})
        }
    } finally {
        loading.value = false
    }
}

async function loadMessages() {
    const res = await api.get(`/api/multi-agent/rooms/${route.params.room_id}/messages/`)
    if (res.data.result === 'success') {
        messages.value = res.data.messages
    }
}

async function loadCharacters() {
    if (!user.id) return
    characters.value = await fetchCharacters(user.id)
}

function addParticipant() {
    settings.value.participants.push({
        character_id: '',
        display_name: `Agent ${settings.value.participants.length + 1}`,
        model_name: '',
        api_base: '',
        use_system_api: true,
        system_prompt: '',
    })
}

function removeParticipant(index) {
    settings.value.participants.splice(index, 1)
}

function onCharacterChange(participant, characterId) {
    // 必须先把 character_id 写回，否则保存时提交的还是旧值（关联角色会丢失）
    participant.character_id = characterId || ''

    const character = characters.value.find(c => String(c.id) === String(characterId))
    if (character) {
        // 显示名还是默认的 Agent N 时自动跟随角色名，用户改过就不动
        if (!participant.display_name || /^Agent\s*\d*$/.test(participant.display_name)) {
            participant.display_name = character.name
        }
        // 关联角色后沿用角色音色，模型与 API 配置保持不变
        if (character.voice?.name) {
            participant.character_voice = character.voice.name
        }
    } else {
        participant.character_voice = ''
    }
}

async function saveSettings() {
    const fd = new FormData()
    Object.entries(settings.value).forEach(([k, v]) => {
        if (k === 'participants') {
            fd.append('participants', JSON.stringify(v))
        } else {
            fd.append(k, v)
        }
    })

    const res = await api.post(`/api/multi-agent/rooms/${room.value.id}/`, fd)
    if (res.data.result === 'success') {
        room.value = res.data.room
        showSettings.value = false
    } else {
        alert(res.data.result)
    }
}

async function sendMessage() {
    const content = inputText.value.trim()
    if (!content || sending.value) return

    sending.value = true
    sendError.value = ''
    inputText.value = ''

    const fd = new FormData()
    fd.append('content', content)
    fd.append('stream', 'true')

    try {
        const token = user.accessToken
        const res = await fetch(
            `${CONFIG_API.HTTP_URL}/api/multi-agent/rooms/${room.value.id}/messages/`,
            {
                method: 'POST',
                body: fd,
                headers: {Authorization: `Bearer ${token}`},
                credentials: 'include',
            }
        )

        if (!res.ok || !res.body) {
            sendError.value = `发送失败（HTTP ${res.status}），请确认已登录`
            return
        }

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
            const {done, value} = await reader.read()
            if (done) break

            buffer += decoder.decode(value, {stream: true})
            const parts = buffer.split('\n\n')
            buffer = parts.pop() || ''

            for (const part of parts) {
                const line = part.trim()
                if (!line.startsWith('data:')) continue

                const payload = JSON.parse(line.slice(5).trim())

                if (payload.type === 'user') {
                    messages.value.push(payload.message)
                } else if (payload.type === 'start') {
                    // 该 agent 开始发言，先占位一条，内容随增量追加
                    streamingMessage.value = {
                        id: `streaming-${payload.speaker_name}-${Date.now()}`,
                        speaker_type: 'agent',
                        speaker_name: payload.speaker_name,
                        content: '',
                    }
                } else if (payload.type === 'delta') {
                    // 增量文本直接追加，气泡实时增长
                    if (streamingMessage.value) {
                        streamingMessage.value.content += payload.content
                    }
                } else if (payload.type === 'notice') {
                    streamingMessage.value = null
                    systemNotices.value.push(payload.content)
                } else if (payload.type === 'agent') {
                    // 发言完成，用落库后的正式消息替换占位
                    streamingMessage.value = null
                    messages.value.push(payload.message)
                    // 后端发言失败时会返回占位文案，明确告知用户原因
                    if (/生成失败/.test(payload.message.content || '')) {
                        sendError.value = '智能体发言失败，请检查房间设置里的模型名是否正确' +
                            '（当前项目可用模型为 deepseek-v4.1-flash）'
                    }
                } else if (payload.type === 'done') {
                    streamingMessage.value = null
                }
            }
            scrollToBottom()
        }
    } catch (e) {
        console.error(e)
        sendError.value = '发送出错，请查看控制台'
    } finally {
        sending.value = false
    }
}

async function clearHistory() {
    if (!confirm('确定清空聊天记录吗？')) return
    const res = await api.delete(`/api/multi-agent/rooms/${room.value.id}/messages/`)
    if (res.data.result === 'success') {
        messages.value = []
    }
}

async function deleteRoom() {
    if (!confirm('确定删除这个房间吗？')) return
    const res = await api.delete(`/api/multi-agent/rooms/${room.value.id}/`)
    if (res.data.result === 'success') {
        router.push({name: 'multi-agent-index'})
    }
}

function scrollToBottom() {
    const el = document.getElementById('agent-chat-body')
    if (el) el.scrollTop = el.scrollHeight
}

onMounted(async () => {
    await loadRoom()
    await Promise.all([loadMessages(), loadCharacters()])
    scrollToBottom()
})

onUnmounted(() => {
    // 离开页面时停止流式接收
})
</script>

<template>
  <div class="h-full flex flex-col">
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <template v-else-if="room">
      <!-- 头部 -->
      <div class="flex items-center gap-3 px-4 py-3 border-b border-base-300">
        <button class="btn btn-ghost btn-sm" @click="router.push({name: 'multi-agent-index'})">返回</button>
        <div class="min-w-0">
          <h1 class="font-bold truncate">{{ room.name }}</h1>
          <p class="text-sm opacity-60 truncate">{{ room.topic || '自由讨论' }}</p>
        </div>
        <div class="ml-auto flex items-center gap-2">
          <div class="avatar-group -space-x-3">
            <div v-for="p in room.participants" :key="p.id" class="avatar">
              <div class="w-8 rounded-full ring ring-base-100">
                <img v-if="p.character_photo" :src="p.character_photo" :alt="p.display_name" />
                <div v-else class="bg-base-300 flex items-center justify-center text-xs">
                  {{ p.display_name.slice(0, 1) }}
                </div>
              </div>
            </div>
          </div>
          <button class="btn btn-ghost btn-sm" @click="showSettings = !showSettings">设置</button>
          <button class="btn btn-ghost btn-sm" @click="clearHistory">清空</button>
          <button class="btn btn-ghost btn-sm text-error" @click="deleteRoom">删除</button>
        </div>
      </div>

      <!-- 设置面板 -->
      <div v-if="showSettings" class="px-4 py-4 bg-base-200 border-b border-base-300 space-y-3">
        <div class="grid gap-3 sm:grid-cols-2">
          <input v-model="settings.name" type="text" placeholder="房间名" class="input input-bordered input-sm w-full" />
          <input v-model="settings.topic" type="text" placeholder="讨论主题" class="input input-bordered input-sm w-full" />
          <input v-model="settings.model_name" type="text" placeholder="模型名" class="input input-bordered input-sm w-full" />
          <input v-model.number="settings.interval_seconds" type="number" min="0" placeholder="发言间隔（秒）" class="input input-bordered input-sm w-full" />
          <label class="form-control w-full">
            <span class="label-text text-xs mb-1">讨论流程</span>
            <select v-model="settings.flow_mode" class="select select-sm w-full">
              <option v-for="m in FLOW_MODES" :key="m.value" :value="m.value">{{ m.label }}</option>
            </select>
          </label>
          <label class="form-control w-full">
            <span class="label-text text-xs mb-1">发言顺序</span>
            <select v-model="settings.turn_order" class="select select-sm w-full">
              <option v-for="o in TURN_ORDERS" :key="o.value" :value="o.value">{{ o.label }}</option>
            </select>
          </label>
        </div>
        <p class="text-xs opacity-60">
          讨论流程：{{ flowHint }}<br />
          发言顺序：{{ turnHint }}
        </p>
        <textarea v-model="settings.system_prompt" placeholder="系统提示词（所有智能体共用）" class="textarea textarea-bordered w-full h-20"></textarea>

        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="font-medium text-sm">参与者</span>
            <button class="btn btn-xs" @click="addParticipant">添加</button>
          </div>
          <div v-for="(p, i) in settings.participants" :key="i" class="flex flex-wrap items-center gap-2 bg-base-100 rounded-lg p-2">
            <select
                v-model="p.character_id"
                class="select select-xs w-40"
                @change="onCharacterChange(p, $event.target.value)"
            >
              <option value="">不关联角色</option>
              <option v-for="c in characters" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
            <input v-model="p.display_name" type="text" placeholder="显示名" class="input input-xs w-32" />
            <span v-if="p.character_voice" class="text-xs opacity-60 self-center whitespace-nowrap">
              音色：{{ p.character_voice }}
            </span>
            <input v-model="p.model_name" type="text" placeholder="模型（留空用默认）" class="input input-xs w-36" />
            <label class="label cursor-pointer gap-1">
              <input v-model="p.use_system_api" type="checkbox" class="checkbox checkbox-xs" />
              <span class="label-text text-xs">系统 API</span>
            </label>
            <template v-if="!p.use_system_api">
              <input v-model="p.api_base" type="text" placeholder="API Base" class="input input-xs w-44" />
              <input v-model="p.api_key" type="password" placeholder="API Key" class="input input-xs w-32" />
            </template>
            <button class="btn btn-ghost btn-xs text-error" @click="removeParticipant(i)">移除</button>
          </div>
        </div>

        <button class="btn btn-primary btn-sm" @click="saveSettings">保存设置</button>
      </div>

      <!-- 消息列表 -->
      <div id="agent-chat-body" class="flex-1 overflow-y-auto p-4 space-y-4">
        <div v-if="messages.length === 0" class="text-center py-20 opacity-60">
          还没有发言，说点什么让智能体们开始讨论吧
        </div>

        <div v-for="msg in displayMessages" :key="msg.id" class="chat" :class="msg.speaker_type === 'human' ? 'chat-end' : 'chat-start'">
          <div class="chat-image">
            <div class="w-9 rounded-full bg-base-300 flex items-center justify-center text-sm">
              {{ msg.speaker_name.slice(0, 1) }}
            </div>
          </div>
          <div class="chat-header text-xs opacity-60 mb-1">
            {{ msg.speaker_name }}
          </div>
          <div
              class="chat-bubble whitespace-pre-wrap"
              :class="msg.speaker_type === 'human' ? 'chat-bubble-primary' : ''"
          >{{ msg.content }}</div>
        </div>

        <!-- 流式接收中的气泡：内容随增量实时增长 -->
        <div v-if="streamingMessage" class="chat chat-start">
          <div class="chat-image">
            <div class="w-9 rounded-full bg-base-300 flex items-center justify-center text-sm">
              {{ streamingMessage.speaker_name.slice(0, 1) }}
            </div>
          </div>
          <div class="chat-header text-xs opacity-60 mb-1">
            {{ streamingMessage.speaker_name }}
            <span class="loading loading-dots loading-xs align-middle ml-1"></span>
          </div>
          <div class="chat-bubble whitespace-pre-wrap">{{ stripMarkdown(streamingMessage.content) }}</div>
        </div>

        <!-- 系统提示 -->
        <div v-for="(notice, i) in systemNotices" :key="'notice' + i"
             class="text-center text-xs opacity-60 py-1">
          {{ notice }}
        </div>
      </div>

      <!-- 输入框 -->
      <div class="px-4 py-3 border-t border-base-300">
        <div v-if="sendError" class="alert alert-error text-sm py-2 mb-2">
          {{ sendError }}
        </div>
        <div class="flex gap-2">
          <input
              v-model="inputText"
              type="text"
              placeholder="发表你的观点…"
              class="input input-bordered flex-1"
              @keydown.enter.prevent="sendMessage"
          />
          <button class="btn btn-primary" :disabled="sending || !inputText.trim()" @click="sendMessage">
            发送
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>

</style>
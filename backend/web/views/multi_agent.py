import json

from django.http import StreamingHttpResponse
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.collaboration import MultiAgentRoom, MultiAgentParticipant, MultiAgentMessage
from web.models.user import UserProfile
from web.services.ai_sse import run_round


def parse_participants(raw):
    """参与者可能是 JSON 数组字符串，也可能被重复表单字段拆成 list，统一解析成 list[dict]"""
    if raw is None:
        return []

    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            raw = json.loads(text)
        except ValueError:
            return []

    if not isinstance(raw, (list, tuple)):
        return []

    return [p for p in raw if isinstance(p, dict)]


def serialize_participant(participant):
    return {
        'id': participant.id,
        'character_id': participant.character_id,
        'character_name': participant.character.name if participant.character else '',
        'character_photo': participant.character.photo.url if participant.character else '',
        'display_name': participant.display_name,
        'model_name': participant.model_name,
        'api_base': participant.api_base,
        # api_key 出于安全不返回给前端
        'use_system_api': participant.use_system_api,
        'system_prompt': participant.system_prompt,
        'order_number': participant.order_number,
        'enabled': participant.enabled,
    }


def serialize_room(room):
    return {
        'id': room.id,
        'name': room.name,
        'topic': room.topic,
        'system_prompt': room.system_prompt,
        'model_name': room.model_name,
        'agent_count': room.agent_count,
        'interval_seconds': room.interval_seconds,
        'flow_mode': room.flow_mode,
        'turn_order': room.turn_order,
        'is_active': room.is_active,
        'participants': [serialize_participant(p) for p in room.participants.all()],
        'create_time': room.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    }


def serialize_message(message):
    return {
        'id': message.id,
        'speaker_type': message.speaker_type,
        'speaker_name': message.speaker_name,
        'content': message.content,
        'turn_number': message.turn_number,
        'create_time': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    }


def create_participants(room, participants_raw):
    """按配置创建房间的参与者，并同步 agent_count。"""
    room.participants.all().delete()
    for index, p in enumerate(participants_raw):
        MultiAgentParticipant.objects.create(
            room=room,
            character_id=p.get('character_id') or None,
            display_name=p.get('display_name', '').strip() or f'Agent {index + 1}',
            model_name=p.get('model_name', '').strip(),
            api_base=p.get('api_base', '').strip(),
            api_key=p.get('api_key', '').strip(),
            use_system_api=p.get('use_system_api', True),
            system_prompt=p.get('system_prompt', '').strip(),
            order_number=index,
            enabled=p.get('enabled', True),
        )
    room.agent_count = len(participants_raw)
    room.save(update_fields=['agent_count'])


class MultiAgentRoomListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            user_profile = UserProfile.objects.get(user=user)
            rooms = MultiAgentRoom.objects.filter(owner=user_profile)

            return Response({
                'result': 'success',
                'rooms': [serialize_room(room) for room in rooms],
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })

    def post(self, request):
        """创建房间，同时保存参与者配置"""
        try:
            user = request.user
            user_profile = UserProfile.objects.get(user=user)

            name = request.data.get('name', '').strip()
            topic = request.data.get('topic', '').strip()
            system_prompt = request.data.get('system_prompt', '').strip()
            model_name = request.data.get('model_name', '').strip() or 'deepseek-chat'
            interval_seconds = int(request.data.get('interval_seconds', 0) or 0)
            flow_mode = request.data.get('flow_mode', 'round_robin')
            turn_order = request.data.get('turn_order', 'configured')
            participants_raw = parse_participants(request.data.get('participants'))

            if not name:
                return Response({
                    'result': '房间名不能为空'
                })

            room = MultiAgentRoom.objects.create(
                owner=user_profile,
                name=name,
                topic=topic,
                system_prompt=system_prompt,
                model_name=model_name,
                interval_seconds=interval_seconds,
                flow_mode=flow_mode,
                turn_order=turn_order,
                agent_count=len(participants_raw),
            )

            create_participants(room, participants_raw)

            return Response({
                'result': 'success',
                'room': serialize_room(room),
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })


class MultiAgentRoomDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        try:
            room = self.get_room(request, room_id)

            return Response({
                'result': 'success',
                'room': serialize_room(room),
            })
        except MultiAgentRoom.DoesNotExist:
            return Response({
                'result': '房间不存在或无权操作'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })

    def post(self, request, room_id):
        try:
            room = self.get_room(request, room_id)

            for field in ['name', 'topic', 'system_prompt', 'model_name', 'flow_mode', 'turn_order']:
                if field in request.data:
                    setattr(room, field, request.data.get(field))

            if 'interval_seconds' in request.data:
                room.interval_seconds = int(request.data.get('interval_seconds') or 0)
            if 'is_active' in request.data:
                room.is_active = request.data.get('is_active')

            room.updated_at = now()
            room.save()

            # 参与者配置整体覆盖
            if 'participants' in request.data:
                participants_raw = parse_participants(request.data.get('participants'))
                create_participants(room, participants_raw)

            return Response({
                'result': 'success',
                'room': serialize_room(room),
            })
        except MultiAgentRoom.DoesNotExist:
            return Response({
                'result': '房间不存在或无权操作'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })

    def delete(self, request, room_id):
        try:
            room = self.get_room(request, room_id)
            room.delete()

            return Response({
                'result': 'success',
            })
        except MultiAgentRoom.DoesNotExist:
            return Response({
                'result': '房间不存在或无权操作'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })

    @staticmethod
    def get_room(request, room_id):
        user_profile = UserProfile.objects.get(user=request.user)
        return MultiAgentRoom.objects.get(id=room_id, owner=user_profile)


class MultiAgentMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        try:
            room = MultiAgentRoomDetailView.get_room(request, room_id)
            messages = MultiAgentMessage.objects.filter(room=room)

            return Response({
                'result': 'success',
                'messages': [serialize_message(m) for m in messages],
            })
        except MultiAgentRoom.DoesNotExist:
            return Response({
                'result': '房间不存在或无权操作'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })

    def delete(self, request, room_id):
        """清空聊天记录"""
        try:
            room = MultiAgentRoomDetailView.get_room(request, room_id)
            MultiAgentMessage.objects.filter(room=room).delete()

            return Response({
                'result': 'success',
            })
        except MultiAgentRoom.DoesNotExist:
            return Response({
                'result': '房间不存在或无权操作'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })

    def post(self, request, room_id):
        """普通请求返回完整结果；stream=true 时走 SSE 逐条推送"""
        try:
            room = MultiAgentRoomDetailView.get_room(request, room_id)
            content = request.data.get('content', '').strip()

            if not content:
                return Response({
                    'result': '发言内容不能为空'
                })

            user_message = MultiAgentMessage.objects.create(
                room=room,
                speaker_type='human',
                speaker_name=room.owner.user.username,
                content=content,
            )

            if request.data.get('stream'):
                return self.stream_response(room, user_message)

            turn_number = self.next_turn_number(room)
            # run_round 产出事件流，这里只收集落库后的完整消息
            agent_messages = [
                payload for event_type, payload in run_round(room, content, turn_number)
                if event_type == 'done'
            ]

            return Response({
                'result': 'success',
                'user_message': serialize_message(user_message),
                'messages': [serialize_message(m) for m in agent_messages],
            })
        except MultiAgentRoom.DoesNotExist:
            return Response({
                'result': '房间不存在或无权操作'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })

    @staticmethod
    def next_turn_number(room):
        last = MultiAgentMessage.objects.filter(room=room).order_by('-turn_number').first()
        return (last.turn_number + 1) if last else 1

    @staticmethod
    def stream_response(room, user_message):
        turn_number = MultiAgentMessageView.next_turn_number(room)

        def event_generator():
            yield f'data: {json.dumps({"type": "user", "message": serialize_message(user_message)}, ensure_ascii=False)}\n\n'

            # run_round 现在产出 ('start'|'delta'|'done'|'notice', payload) 事件
            for event_type, payload in run_round(room, user_message.content, turn_number):
                if event_type == 'start':
                    data = {'type': 'start', 'speaker_name': payload['speaker_name']}
                elif event_type == 'delta':
                    data = {'type': 'delta', 'content': payload}
                elif event_type == 'notice':
                    data = {'type': 'notice', 'content': payload}
                else:  # done
                    data = {'type': 'agent', 'message': serialize_message(payload)}

                yield f'data: {json.dumps(data, ensure_ascii=False)}\n\n'

            yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'

        response = StreamingHttpResponse(event_generator(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
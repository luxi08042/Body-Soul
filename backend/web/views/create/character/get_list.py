from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response

from web.models.character import Character
from web.models.user import UserProfile


class GetListCharacterView(APIView):
    def get(self, request):
        try:
            items_count = int(request.query_params.get('items_count') or 0)

            # 不传 user_id 时默认查当前登录用户自己的角色
            user_id_param = request.query_params.get('user_id')
            if user_id_param:
                user_id = int(user_id_param)
            else:
                if not request.user.is_authenticated:
                    return Response({'result': '请先登录'})
                user_id = request.user.id

            user = User.objects.get(id=user_id)
            user_profile = UserProfile.objects.get(user=user)
            characters_raw = Character.objects.filter(
                author=user_profile
            ).order_by('-id')[items_count: items_count + 20]
            characters = []
            for character in characters_raw:
                author = character.author
                characters.append({
                    'id': character.id,
                    'name': character.name,
                    'profile': character.profile,
                    'photo': character.photo.url,
                    'background_image': character.background_image.url,
                    # 关联角色时前端要显示音色
                    'voice': character.voice.name if character.voice else '',
                    'author': {
                        'user_id': author.user_id,
                        'username': author.user.username,
                        'photo': author.photo.url,
                    }
                })
            return Response({
                'result': 'success',
                'user_profile': {
                    'user_id': user.id,
                    'username': user.username,
                    'profile': user_profile.profile,
                    'photo': user_profile.photo.url,
                },
                'characters': characters,
            })
        except User.DoesNotExist:
            return Response({
                'result': '用户不存在'
            })
        except ValueError:
            return Response({
                'result': '请求参数不正确'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })
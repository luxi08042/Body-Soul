<script setup>
import Photo from "@/views/create/character/components/Photo.vue";
import Name from "@/views/create/character/components/Name.vue";
import Profile from "@/views/create/character/components/Profile.vue";
import BackgroundImage from "@/views/create/character/components/BackgroundImage.vue";
import {onMounted, ref, useTemplateRef} from "vue";
import {base64ToFile} from "@/js/utils/base64_to_file.js";
import api from "@/js/http/api.js";
import {useRoute, useRouter} from "vue-router";
import {useUserStore} from "@/stores/user.js";
import Voice from "@/views/create/character/components/Voice.vue";
import {fetchVoices} from "@/js/api/character.js";

const user = useUserStore()
const router = useRouter()
const route = useRoute()
const characterId = route.params.character_id
const character = ref(null)

const voices = ref([])
const curVoiceId = ref(null)

/** 仅刷新音色列表（删除音色后调用），保留当前角色的其他数据 */
async function reloadVoices(keepEmpty = false) {
  voices.value = await fetchVoices()
  if (keepEmpty) {
    curVoiceId.value = null
  } else if (!voices.value.find(v => String(v.id) === String(curVoiceId.value))) {
    curVoiceId.value = voices.value.length ? voices.value[0].id : null
  }
}

/** @removed 的第二参表示"刚删掉的正是当前选中"，此时保持未选择 */
function handleRemovedVoice(id, keepEmpty) {
  reloadVoices(keepEmpty)
}

const photoRef = useTemplateRef('photo-ref')
const nameRef = useTemplateRef('name-ref')
const voiceRef = useTemplateRef('voice-ref')
const profileRef = useTemplateRef('profile-ref')
const backgroundImageRef = useTemplateRef('background-image-ref')
const errorMessage = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/api/create/character/get_single/', {
      params: {
        character_id: characterId,
      }
    })
    const data = res.data
    if (data.result === 'success') {
      character.value = data.character
      voices.value = data.voices || []
      curVoiceId.value = data.character.voice_id || (voices.value[0]?.id ?? null)
    } else {
      // 加载失败要给出提示，否则页面因 v-if="character" 直接空白
      errorMessage.value = data.result || '角色信息加载失败'
    }
  } catch (err) {
    errorMessage.value = '角色信息加载失败，请稍后重试'
  }
})

async function handleUpdate() {
  const photo = photoRef.value.myPhoto
  const name = nameRef.value.myName?.trim()
  const voice = voiceRef.value.myVoice
  const profile = profileRef.value.myProfile?.trim()
  const backgroundImage = backgroundImageRef.value.myBackgroundImage

  errorMessage.value = ''
  if (!photo) {
    errorMessage.value = '头像不能为空'
  } else if (!name) {
    errorMessage.value = '名字不能为空'
  } else if (!voice) {
    errorMessage.value = '音色不能为空'
  } else if (!profile) {
    errorMessage.value = '角色介绍不能为空'
  } else if (!backgroundImage) {
    errorMessage.value = '聊天背景不能为空'
  } else {
    const formData = new FormData()
    formData.append('character_id', characterId)
    formData.append('name', name)
    formData.append('voice_id', voice)
    formData.append('profile', profile)

    if (photo !== character.value.photo) {
      formData.append('photo', base64ToFile(photo, 'photo.png'))
    }

    if (backgroundImage !== character.value.background_image) {
      formData.append('background_image', base64ToFile(backgroundImage, 'background_image.png'))
    }

    try {
      const res = await api.post('/api/create/character/update/', formData)
      const data = res.data
      if (data.result === 'success') {
        await router.push({
          name: 'user-space-index',
          params: {
            user_id: user.id,
          }
        })
      } else {
        errorMessage.value = data.result
      }
    } catch (err) {
    }
  }
}
</script>

<template>
  <!-- 加载失败时给出提示，而不是整页空白 -->
  <div v-if="!character" class="flex justify-center mt-24">
    <div class="alert alert-error max-w-md">
      <span>{{ errorMessage || '角色信息加载中…' }}</span>
    </div>
  </div>

  <div v-else class="flex justify-center">
    <div class="card w-120 bg-base-200 shadow-sm mt-16">
      <div class="card-body">
        <h3 class="text-lg font-bold my-4">更新角色</h3>
        <Photo ref="photo-ref" :photo="character.photo" />
        <Name ref="name-ref" :name="character.name" />
        <Voice ref="voice-ref" :voices="voices" :curVoiceId="curVoiceId" @removed="handleRemovedVoice" />
        <Profile ref="profile-ref" :profile="character.profile" />
        <BackgroundImage ref="background-image-ref" :backgroundImage="character.background_image" />

        <p v-if="errorMessage" class="text-sm text-red-500">{{ errorMessage }}</p>

        <div class="flex justify-center">
          <button @click="handleUpdate" class="btn btn-neutral w-60 mt-2">更新</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>
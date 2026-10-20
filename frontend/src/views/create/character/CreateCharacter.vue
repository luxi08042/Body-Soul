<script setup>
import Photo from "@/views/create/character/components/Photo.vue";
import Name from "@/views/create/character/components/Name.vue";
import Profile from "@/views/create/character/components/Profile.vue";
import BackgroundImage from "@/views/create/character/components/BackgroundImage.vue";
import {onMounted, ref, useTemplateRef} from "vue";
import {base64ToFile} from "@/js/utils/base64_to_file.js";
import api from "@/js/http/api.js";
import {useRouter} from "vue-router";
import {useUserStore} from "@/stores/user.js";
import Voice from "@/views/create/character/components/Voice.vue";
import {fetchVoices} from "@/js/api/character.js";
import VoiceRecorder from "@/views/create/character/components/voicerecorder/VoiceRecorder.vue";

const user = useUserStore()
const router = useRouter()

const photoRef = useTemplateRef('photo-ref')
const nameRef = useTemplateRef('name-ref')
const voiceRef = useTemplateRef('voice-ref')
const profileRef = useTemplateRef('profile-ref')
const backgroundImageRef = useTemplateRef('background-image-ref')
const errorMessage = ref('')

const voices = ref([])
const curVoiceId = ref(null)

/** 拉取音色列表；selectId 传入时自动选中该音色 */
async function loadVoices(selectId = null, keepEmpty = false) {
  voices.value = await fetchVoices()
  if (selectId) {
    curVoiceId.value = selectId
  } else if (keepEmpty) {
    // 刚删掉了正在使用的音色，保持未选择状态
    curVoiceId.value = null
  } else if (!voices.value.find(v => String(v.id) === String(curVoiceId.value))) {
    // 当前选中的音色可能已被删除，回退到第一个
    curVoiceId.value = voices.value.length ? voices.value[0].id : null
  }
}

/** 音色被删除后刷新列表；keepEmpty 为 true 时保持"未选择" */
function handleRemovedVoice(id, keepEmpty) {
  loadVoices(null, keepEmpty)
}

onMounted(() => loadVoices())

async function handleClonedVoice(voice) {
  // 复刻成功后刷新音色列表并自动选中新音色
  await loadVoices(voice.id)
}

async function handleCreate() {
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
    formData.append('name', name)
    formData.append('voice_id', voice)
    formData.append('profile', profile)
    formData.append('photo', base64ToFile(photo, 'photo.png'))
    formData.append('background_image', base64ToFile(backgroundImage, 'background_image.png'))

    try {
      const res = await api.post('/api/create/character/create/', formData)
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
  <div class="flex justify-center">
    <div class="card w-120 bg-base-200 shadow-sm mt-16">
      <div class="card-body">
        <h3 class="text-lg font-bold my-4">创建角色</h3>
        <Photo ref="photo-ref" />
        <Name ref="name-ref" />
        <Voice ref="voice-ref" :voices="voices" :curVoiceId="curVoiceId" @removed="handleRemovedVoice" />
        <VoiceRecorder @cloned="handleClonedVoice" />
        <Profile ref="profile-ref" />
        <BackgroundImage ref="background-image-ref" />

        <p v-if="errorMessage" class="text-sm text-red-500">{{ errorMessage }}</p>

        <div class="flex justify-center">
          <button @click="handleCreate" class="btn btn-neutral w-60 mt-2">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>
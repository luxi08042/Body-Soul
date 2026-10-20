<script setup>
import {computed, onUnmounted, ref} from "vue";
import api from "@/js/http/api.js";

const emit = defineEmits(['cloned'])

const recording = ref(false)
const submitting = ref(false)
const duration = ref(0)
const audioBlob = ref(null)
const audioUrl = ref('')
const voiceName = ref('')
const errorMsg = ref('')

// navigator 是浏览器全局对象，不能直接在模板里引用，放到 script 里判断
const canRecord = computed(() => {
    return typeof navigator !== 'undefined' && !!navigator.mediaDevices
})

let mediaRecorder = null
let chunks = []
let timer = null
let stream = null

async function startRecording() {
    errorMsg.value = ''
    if (!canRecord.value) {
        errorMsg.value = '当前浏览器不支持录音，请用 Chrome / Edge 并允许麦克风权限'
        return
    }
    if (recording.value) return

    try {
        stream = await navigator.mediaDevices.getUserMedia({audio: true})
    } catch (e) {
        errorMsg.value = '无法访问麦克风，请检查浏览器权限设置'
        return
    }

    chunks = []
    mediaRecorder = new MediaRecorder(stream)
    mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) chunks.push(e.data)
    }

    mediaRecorder.start()
    recording.value = true
    duration.value = 0

    timer = setInterval(() => {
        duration.value += 1
        // 最多录 60 秒，超时自动停止
        if (duration.value >= 60) stopRecording()
    }, 1000)
}

function stopRecording() {
    if (!mediaRecorder) return

    const recorder = mediaRecorder
    recorder.onstop = () => {
        // 必须在 mediaRecorder 置空前把数据取出来
        const mimeType = recorder.mimeType || 'audio/webm'
        const blob = new Blob(chunks, {type: mimeType})
        if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
        audioBlob.value = blob
        audioUrl.value = URL.createObjectURL(blob)
    }

    recorder.stop()
    recording.value = false
    mediaRecorder = null

    if (timer) {
        clearInterval(timer)
        timer = null
    }

    if (stream) {
        stream.getTracks().forEach(t => t.stop())
        stream = null
    }
}

function resetRecording() {
    if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
    audioBlob.value = null
    audioUrl.value = ''
    duration.value = 0
}

async function submitClone() {
    errorMsg.value = ''
    if (!audioBlob.value) {
        errorMsg.value = '请先录制一段音频'
        return
    }
    if (!voiceName.value.trim()) {
        errorMsg.value = '请填写音色名称'
        return
    }

    submitting.value = true
    try {
        // 浏览器录音默认是 webm/opus，百炼只接受 mp3/wav/m4a，必须先转码
        let payload = audioBlob.value
        let ext = 'webm'
        try {
            const converted = await toWav(audioBlob.value)
            payload = converted.blob
            ext = 'wav'
        } catch (e) {
            console.warn('转 wav 失败，退回原始音频', e)
            // 转码失败时按原始 mime 猜一个后缀
            const type = audioBlob.value.type || ''
            ext = type.includes('mp4') ? 'm4a' : type.includes('ogg') ? 'ogg' : 'webm'
        }

        const fd = new FormData()
        fd.append('name', voiceName.value.trim())
        fd.append('audio', new File([payload], `sample.${ext}`, {type: payload.type}))

        const res = await api.post('/api/create/character/voice/clone_voice/', fd)
        if (res.data.result === 'success') {
            emit('cloned', res.data.voice)
            voiceName.value = ''
            resetRecording()
        } else {
            // 后端会透出百炼的具体原因，这里针对常见情况给可操作的提示
            const raw = res.data.result || '音色复刻失败，请稍后重试'
            if (/download audio failed|InputDownloadFailed/i.test(raw)) {
                errorMsg.value = '云端无法拉取这段音频。本地开发需要在 .env 里配置 PUBLIC_BASE_URL（内网穿透地址）。'
            } else {
                errorMsg.value = raw
            }
        }
    } catch (e) {
        errorMsg.value = '音色复刻失败，请稍后重试'
    } finally {
        submitting.value = false
    }
}

/** 用 WebAudio 把任意音频解码后重编码成 16bit PCM 的 wav */
async function toWav(blob) {
    const arrayBuffer = await blob.arrayBuffer()
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
    await audioContext.close()

    const numChannels = audioBuffer.numberOfChannels
    const sampleRate = audioBuffer.sampleRate
    const numFrames = audioBuffer.length
    const bytesPerSample = 2
    const blockAlign = numChannels * bytesPerSample
    const dataSize = numFrames * blockAlign
    const buffer = new ArrayBuffer(44 + dataSize)
    const view = new DataView(buffer)

    // 写 RIFF 头
    writeString(view, 0, 'RIFF')
    view.setUint32(4, 36 + dataSize, true)
    writeString(view, 8, 'WAVE')
    writeString(view, 12, 'fmt ')
    view.setUint32(16, 16, true)           // fmt chunk 大小
    view.setUint16(20, 1, true)            // PCM
    view.setUint16(22, numChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * blockAlign, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, 16, true)           // 位深
    writeString(view, 36, 'data')
    view.setUint32(40, dataSize, true)

    // 各声道数据交织写入
    const channels = []
    for (let c = 0; c < numChannels; c++) {
        channels.push(audioBuffer.getChannelData(c))
    }

    let offset = 44
    for (let i = 0; i < numFrames; i++) {
        for (let c = 0; c < numChannels; c++) {
            // 限幅后转 16bit 有符号整数
            const sample = Math.max(-1, Math.min(1, channels[c][i]))
            view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
            offset += 2
        }
    }

    return {blob: new Blob([buffer], {type: 'audio/wav'})}
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i))
    }
}

onUnmounted(() => {
    if (timer) clearInterval(timer)
    if (stream) stream.getTracks().forEach(t => t.stop())
    if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
})
</script>

<template>
  <div class="fieldset border border-base-300 rounded-xl p-4 space-y-3">
    <label class="label text-base">音色复刻</label>
    <p class="text-sm opacity-60 -mt-1">录一段你的声音，生成专属音色（建议 10 秒以上，清晰无杂音）</p>

    <div class="flex flex-wrap items-center gap-3">
      <button
          v-if="!recording"
          class="btn btn-sm"
          :class="{'btn-disabled': !canRecord}"
          @click="startRecording"
      >
        开始录音
      </button>

      <template v-else>
        <span class="badge badge-error gap-2">
          <span class="loading loading-ring loading-xs"></span>
          录音中 {{ duration }}s
        </span>
        <button class="btn btn-sm btn-neutral" @click="stopRecording">停止录音</button>
      </template>

      <span v-if="!recording && audioBlob" class="text-sm opacity-70">
        已录制 {{ duration }} 秒
      </span>
      <button v-if="audioBlob && !recording" class="btn btn-ghost btn-xs" @click="resetRecording">重录</button>
    </div>

    <p v-if="!canRecord" class="text-sm text-warning">
      当前浏览器不支持录音，或页面不是通过 localhost / https 访问。请用 Chrome / Edge 打开并允许麦克风权限。
    </p>

    <audio v-if="audioUrl" :src="audioUrl" controls class="w-full"></audio>

    <div class="flex flex-wrap items-end gap-3">
      <div class="form-control flex-1 min-w-40">
        <label class="label text-sm py-1">音色名称</label>
        <input
            v-model="voiceName"
            type="text"
            placeholder="给我的音色起个名字"
            class="input input-bordered input-sm w-full"
        />
      </div>
      <button
          class="btn btn-primary btn-sm"
          :disabled="submitting || !audioBlob"
          @click="submitClone"
          :title="audioBlob ? '' : '请先完成录音'"
      >
        <span v-if="submitting" class="loading loading-spinner loading-xs"></span>
        开始复刻
      </button>
    </div>

    <div v-if="!audioBlob && !recording" class="text-xs opacity-50">
      需先完成录音并填写音色名称，「开始复刻」才会可用
    </div>

    <div v-if="errorMsg" class="alert alert-error text-sm py-2">{{ errorMsg }}</div>
  </div>
</template>

<style scoped>

</style>
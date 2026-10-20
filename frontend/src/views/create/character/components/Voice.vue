<script setup>
import {computed, ref, watch} from "vue";
import api from "@/js/http/api.js";

const props = defineProps({
  voices: {type: Array, default: () => []},
  curVoiceId: {type: [Number, String], default: null},
})
const emit = defineEmits(['removed'])

const myVoice = ref(props.curVoiceId)
const open = ref(false)
const deletingId = ref(null)
const errorMsg = ref('')

watch(() => props.curVoiceId, newVal => {
  myVoice.value = newVal
})

const currentName = computed(() =>
    props.voices.find(v => String(v.id) === String(myVoice.value))?.name || '请选择音色'
)

function select(id) {
  myVoice.value = id
  open.value = false
}

async function remove(voice, e) {
  // 阻止冒泡，避免点 × 时同时选中该音色或收起下拉
  e.stopPropagation()

  if (voice.used_count > 0) {
    errorMsg.value = `「${voice.name}」正被 ${voice.used_count} 个角色使用，无法删除`
    return
  }
  if (!confirm(`确定删除音色「${voice.name}」吗？此操作不可恢复。`)) return

  deletingId.value = voice.id
  errorMsg.value = ''
  try {
    const fd = new FormData()
    fd.append('voice_id', String(voice.id))
    const res = await api.post('/api/create/character/voice/delete/', fd)

    if (res.data.result === 'success') {
      // 删掉的正好是当前选中的音色：置空并通知父组件不要自动回填，
      // 否则用户会看到下拉框跳到别的音色，以为删除没生效
      const wasSelected = String(myVoice.value) === String(voice.id)
      if (wasSelected) {
        myVoice.value = null
      }
      emit('removed', voice.id, wasSelected)
    } else {
      errorMsg.value = res.data.result || '删除失败，请稍后重试'
    }
  } catch (err) {
    errorMsg.value = err?.response?.data?.result || '删除失败，请稍后重试'
  } finally {
    deletingId.value = null
  }
}

defineExpose({
  myVoice,
})
</script>

<template>
  <fieldset class="fieldset">
    <label class="label text-base">音色</label>

    <!-- 自定义下拉：原生 select 无法在选项里放删除按钮 -->
    <div class="relative">
      <!-- 遮罩层放最底层，仅用于捕获外部点击，不遮挡下拉本身 -->
      <div v-if="open" class="fixed inset-0 z-10" @click="open = false"></div>

      <button
          type="button"
          class="select w-full flex items-center justify-between relative z-20"
          @click="open = !open"
      >
        <span :class="currentName === '请选择音色' ? 'opacity-60' : ''">{{ currentName }}</span>
        <span class="text-xs opacity-60">▾</span>
      </button>

      <div
          v-if="open"
          class="absolute z-30 mt-1 w-full max-h-64 overflow-y-auto bg-base-100 border border-base-300 rounded-lg shadow-lg"
      >
        <div
            v-for="voice in voices"
            :key="voice.id"
            class="flex items-center gap-2 px-3 py-2 hover:bg-base-200 cursor-pointer"
        >
          <!-- 选项主体：点击选中 -->
          <span
              class="flex-1 min-w-0 flex items-center gap-2"
              @click="select(voice.id)"
          >
            <span class="truncate">{{ voice.name }}</span>
            <span v-if="voice.used_count > 0" class="badge badge-ghost badge-xs shrink-0">
              {{ voice.used_count }} 个角色在用
            </span>
          </span>

          <!-- 删除按钮 -->
          <button
              type="button"
              class="btn btn-ghost btn-xs btn-circle text-error shrink-0"
              :disabled="deletingId === voice.id"
              :title="voice.used_count > 0 ? '该音色正被角色使用，无法删除' : '删除该音色'"
              @click="remove(voice, $event)"
          >
            <span v-if="deletingId === voice.id" class="loading loading-spinner loading-xs"></span>
            <span v-else>✕</span>
          </button>
        </div>

        <div v-if="voices.length === 0" class="px-3 py-4 text-sm opacity-60 text-center">
          还没有音色
        </div>
      </div>
    </div>

    <p v-if="errorMsg" class="text-error text-xs mt-1">{{ errorMsg }}</p>
  </fieldset>
</template>

<style scoped>

</style>
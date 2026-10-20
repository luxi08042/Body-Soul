<script setup>
import {computed, ref, watch} from "vue";
import {useRouter} from "vue-router";
import api from "@/js/http/api.js";

const props = defineProps({
  blog: {type: Object, required: true},
  canEdit: {type: Boolean, default: false},
})
const emit = defineEmits(['remove', 'updated'])

const router = useRouter()

const editing = ref(false)
const saving = ref(false)
const titleInput = ref('')
const contentInput = ref('')
const tagsInput = ref('')
const coverFile = ref(null)
// 编辑态下的公开/私密开关
const isPublicInput = ref(true)
// 本地保存的封面地址，保存成功后立即覆盖，避免依赖父组件刷新导致封面看起来没变
const localCover = ref('')
// 封面 URL 的缓存破坏参数，换封面后自增
const coverVersion = ref(0)
const errorMsg = ref('')

/** 当前应展示的封面地址 */
const displayCover = computed(() => {
  const url = localCover.value || props.blog.cover_photo
  if (!url) return ''
  return `${url}${url.includes('?') ? '&' : '?'}v=${coverVersion.value}`
})

watch(() => props.blog.cover_photo, newUrl => {
  // 父组件刷回新数据时同步本地状态
  if (newUrl && newUrl !== localCover.value) {
    localCover.value = newUrl
  }
})

function startEdit() {
  titleInput.value = props.blog.title
  contentInput.value = props.blog.content
  tagsInput.value = (props.blog.tags || []).join(' ')
  isPublicInput.value = props.blog.is_public !== false
  coverFile.value = null
  errorMsg.value = ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  errorMsg.value = ''
}

function onCoverChange(e) {
  coverFile.value = e.target.files[0] || null
  // 选完立刻清空 DOM 值，保证下次选同一个文件也能再次触发 change
  // （否则浏览器认为值没变，不会再触发 change 事件）
  e.target.value = ''
}

async function save() {
  if (!titleInput.value.trim()) {
    errorMsg.value = '标题不能为空'
    return
  }
  if (!contentInput.value.trim()) {
    errorMsg.value = '正文不能为空'
    return
  }

  saving.value = true
  errorMsg.value = ''
  try {
    const fd = new FormData()
    fd.append('blog_id', props.blog.id)
    fd.append('title', titleInput.value.trim())
    fd.append('content', contentInput.value)
fd.append('tags', JSON.stringify(tagsInput.value.split(/[\s,，]+/).filter(Boolean)))
      fd.append('is_public', isPublicInput.value ? 'true' : 'false')
      // 只有用户重新选了封面才上传；不选就保持原封面不变
      if (coverFile.value) {
      fd.append('cover_photo', coverFile.value)
    }

    const res = await api.post('/api/blog/update/', fd)
    if (res.data.result === 'success') {
      // 后端已返回最新数据，直接更新本地，不再等父组件二次请求
      if (res.data.blog) {
        localCover.value = res.data.blog.cover_photo || ''
        // 版本号自增，强制浏览器重新拉取新封面
        coverVersion.value += 1
        emit('updated', props.blog.id, res.data.blog)
      } else {
        emit('updated', props.blog.id)
      }
      editing.value = false
    } else {
      errorMsg.value = res.data.result
    }
  } catch (e) {
    errorMsg.value = '保存失败，请稍后重试'
  } finally {
    saving.value = false
  }
}

/** 快速切换公开 / 私密 */
async function togglePublic() {
  const next = !props.blog.is_public
  if (!next && !confirm('设为私密后，其他人将无法查看这篇博客。确定继续吗？')) return

  const fd = new FormData()
  fd.append('blog_id', String(props.blog.id))
  fd.append('title', props.blog.title)
  fd.append('content', props.blog.content)
  fd.append('tags', JSON.stringify(props.blog.tags || []))
  fd.append('is_public', next ? 'true' : 'false')

  try {
    const res = await api.post('/api/blog/update/', fd)
    if (res.data.result === 'success') {
      emit('updated', props.blog.id, res.data.blog)
    } else {
      errorMsg.value = res.data.result
    }
  } catch (e) {
    errorMsg.value = e?.response?.data?.result || '操作失败，请稍后重试'
  }
}

function openDetail() {
  router.push({name: 'blog-detail', params: {blog_id: props.blog.id}})
}

const showConfirm = ref(false)

async function handleRemove() {
  const fd = new FormData()
  fd.append('blog_id', props.blog.id)
  const res = await api.post('/api/blog/remove/', fd)
  if (res.data.result === 'success') {
    showConfirm.value = false
    emit('remove', props.blog.id)
  } else {
    alert(res.data.result)
  }
}
</script>

<template>
  <div class="card bg-base-100 shadow-sm hover:shadow-lg transition-shadow w-full">
    <!-- 展示态 -->
    <template v-if="!editing">
      <figure v-if="displayCover" class="h-32 cursor-pointer" @click="openDetail">
        <img :src="displayCover" :alt="blog.title" class="w-full object-cover" />
      </figure>

      <div class="card-body p-4">
        <h3 class="card-title text-base cursor-pointer hover:text-primary transition-colors"
            @click="openDetail">
          {{ blog.title }}
        </h3>

        <p v-if="blog.content" class="text-sm opacity-70 line-clamp-2">
          {{ blog.content.replace(/[#*`>\-]/g, '').slice(0, 60) }}
        </p>

        <div v-if="blog.tags && blog.tags.length" class="flex flex-wrap gap-1">
          <span v-for="tag in blog.tags" :key="tag" class="badge badge-sm badge-outline">{{ tag }}</span>
        </div>

        <div class="flex items-center gap-2 mt-2">
          <span class="text-sm opacity-60">{{ blog.create_time.slice(0, 10) }}</span>
          <!-- 公开 / 私密标识 -->
          <span class="badge badge-xs"
                :class="blog.is_public === false ? 'badge-warning' : 'badge-ghost'">
            {{ blog.is_public === false ? '私密' : '公开' }}
          </span>
          <div v-if="canEdit" class="ml-auto flex gap-1">
            <button class="btn btn-ghost btn-xs" @click="togglePublic">
              {{ blog.is_public === false ? '设为公开' : '设为私密' }}
            </button>
            <button class="btn btn-ghost btn-xs" @click="startEdit">编辑</button>
            <button class="btn btn-ghost btn-xs text-error" @click="showConfirm = true">删除</button>
          </div>
          <button v-else class="btn btn-ghost btn-xs ml-auto" @click="openDetail">查看</button>
        </div>
      </div>
    </template>

    <!-- 编辑态 -->
    <div v-else class="card-body p-4 space-y-3">
      <input v-model="titleInput" type="text" placeholder="标题"
             class="input input-bordered input-sm w-full" />
      <textarea v-model="contentInput" placeholder="正文，支持 Markdown"
                class="textarea textarea-bordered w-full h-40 leading-relaxed text-sm"></textarea>
      <input v-model="tagsInput" type="text" placeholder="标签，空格分隔"
             class="input input-bordered input-sm w-full" />

      <label class="label cursor-pointer gap-2 justify-start">
        <input v-model="isPublicInput" type="checkbox" class="checkbox checkbox-sm" />
        <span class="label-text text-xs">
          {{ isPublicInput ? '公开（所有人可见）' : '私密（仅自己可见）' }}
        </span>
      </label>

      <label class="btn btn-xs self-start">
        {{ coverFile ? '已选新封面' : (displayCover ? '更换封面' : '选择封面') }}
        <input type="file" accept="image/*" class="hidden" @change="onCoverChange" />
      </label>

      <div v-if="errorMsg" class="text-error text-xs">{{ errorMsg }}</div>

      <div class="flex gap-2">
        <button class="btn btn-primary btn-xs" :disabled="saving" @click="save">
          <span v-if="saving" class="loading loading-spinner loading-xs"></span>
          保存
        </button>
        <button class="btn btn-ghost btn-xs" :disabled="saving" @click="cancelEdit">取消</button>
      </div>
    </div>

    <div v-if="showConfirm" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg">删除博客</h3>
        <p class="py-4">确定要删除《{{ blog.title }}》吗？此操作不可恢复。</p>
        <div class="modal-action">
          <button class="btn" @click="showConfirm = false">取消</button>
          <button class="btn btn-error" @click="handleRemove">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>
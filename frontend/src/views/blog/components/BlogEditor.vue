<script setup>
import {computed, ref, watch} from "vue";
import api from "@/js/http/api.js";
import BlogDetailContent from "@/views/blog/BlogDetailContent.vue";

const props = defineProps({
    blog: {   // 传入则为编辑模式，不传为新建
        type: Object,
        default: null,
    },
    submitting: Boolean,
})

const emit = defineEmits(['submit'])

const title = ref('')
const content = ref('')
const tagsInput = ref('')
const coverPhoto = ref(null)
const previewMode = ref(false)
// 默认公开；编辑时沿用原设置
const isPublic = ref(true)

const isEdit = computed(() => !!props.blog)

watch(() => props.blog, newBlog => {
    if (newBlog) {
        title.value = newBlog.title
        content.value = newBlog.content
        tagsInput.value = (newBlog.tags || []).join(' ')
        isPublic.value = newBlog.is_public !== false
    }
}, {immediate: true})

function onCoverChange(e) {
    coverPhoto.value = e.target.files[0] || null
}

async function uploadInlineImage(file) {
    const formData = new FormData()
    formData.append('image', file)
    try {
        const res = await api.post('/api/blog/upload-image/', formData)
        if (res.data.result === 'success') {
            return res.data.url
        }
    } catch (e) {
        console.error('图片上传失败', e)
    }
    return ''
}

function insertImage(e) {
    const file = e.target.files[0]
    if (!file) return
    uploadInlineImage(file).then(url => {
        if (url) {
            content.value += `\n![图片](${url})\n`
        }
    })
    e.target.value = ''
}

function handleSubmit() {
    emit('submit', {
        title: title.value.trim(),
        content: content.value,
        tags: JSON.stringify(tagsInput.value.split(/[\s,，]+/).filter(Boolean)),
        cover_photo: coverPhoto.value,
        is_public: isPublic.value,
    })
}
</script>

<template>
  <div class="max-w-3xl mx-auto w-full space-y-4">
    <div class="form-control">
      <input
          v-model="title"
          type="text"
          placeholder="给文章起个标题"
          class="input input-bordered input-lg w-full"
      />
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <label class="btn btn-sm">
        选择封面
        <input type="file" accept="image/*" class="hidden" @change="onCoverChange" />
      </label>
      <span v-if="coverPhoto" class="text-sm opacity-70">{{ coverPhoto.name }}</span>

      <label class="btn btn-sm">
        插入图片
        <input type="file" accept="image/*" class="hidden" @change="insertImage" />
      </label>

      <label class="btn btn-sm ml-auto" @click="previewMode = !previewMode">
        {{ previewMode ? '继续编辑' : '预览' }}
      </label>
    </div>

    <input
        v-if="!previewMode"
        v-model="content"
        type="text"
        placeholder="支持 Markdown 语法：# 标题、**粗体**、- 列表、> 引用、`代码`"
        class="textarea textarea-bordered w-full h-96 leading-relaxed font-mono text-sm"
    />
    <div v-else class="border border-base-300 rounded-lg p-4 min-h-96">
      <BlogDetailContent :blog="{title, content, tags: tagsInput.split(/[\s,，]+/).filter(Boolean), username: '', photo: '', create_time: ''}" />
    </div>

    <div class="form-control">
      <input
          v-model="tagsInput"
          type="text"
          placeholder="标签，用空格分隔，例如：AI 陪伴 情感"
          class="input input-bordered w-full"
      />
    </div>

    <!-- 公开 / 私密 -->
    <div class="form-control">
      <div class="flex items-center justify-between bg-base-200 rounded-lg px-4 py-3">
        <div class="min-w-0">
          <div class="font-medium">{{ isPublic ? '公开博客' : '私密博客' }}</div>
          <div class="text-xs opacity-60">
            {{ isPublic ? '所有人可以在博客列表和你的空间看到这篇博客'
                        : '仅你自己可见，不会在博客列表和个人空间展示' }}
          </div>
        </div>
        <input
            v-model="isPublic"
            type="checkbox"
            class="toggle toggle-primary shrink-0"
        />
      </div>
    </div>

    <button
        class="btn btn-primary w-full"
        :disabled="submitting"
        @click="handleSubmit"
    >
      <span v-if="submitting" class="loading loading-spinner loading-sm"></span>
      {{ isEdit ? '保存修改' : '发布博客' }}
    </button>
  </div>
</template>

<style scoped>

</style>
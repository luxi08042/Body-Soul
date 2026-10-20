<script setup>
import {onMounted, ref} from "vue";
import {useRouter} from "vue-router";
import api from "@/js/http/api.js";
import {useUserStore} from "@/stores/user.js";
import {fetchCharacters} from "@/js/api/character.js";
import AgentChatIcon from "@/components/navbar/icons/AgentChatIcon.vue";

const router = useRouter()
const user = useUserStore()

const rooms = ref([])
const characters = ref([])
const loading = ref(true)
const showCreate = ref(false)

const form = ref({name: '', topic: '', model_name: 'deepseek-v4.1-flash', participants: []})

const FLOW_LABELS = {
    round_robin: '轮流发言',
    moderated: '主持人串联',
    free: '自由讨论',
}

async function loadRooms() {
    loading.value = true
    try {
        const res = await api.get('/api/multi-agent/rooms/')
        if (res.data.result === 'success') {
            rooms.value = res.data.rooms
        }
    } finally {
        loading.value = false
    }
}

async function loadCharacters() {
    if (!user.id) return
    characters.value = await fetchCharacters(user.id)
}

function addParticipant() {
    form.value.participants.push({
        character_id: '',
        display_name: `Agent ${form.value.participants.length + 1}`,
        system_prompt: '',
    })
}

function removeParticipant(index) {
    form.value.participants.splice(index, 1)
}

function onCharacterChange(p, characterId) {
    // 必须写回 character_id，否则提交时关联信息为空
    p.character_id = characterId || ''

    const c = characters.value.find(x => String(x.id) === String(characterId))
    if (c) {
        // 显示名仍是默认的 Agent N 时跟随角色名
        if (!p.display_name || /^Agent\s*\d*$/.test(p.display_name)) {
            p.display_name = c.name
        }
        p.character_voice = c.voice?.name || ''
    } else {
        p.character_voice = ''
    }
}

async function createRoom() {
    if (!form.value.name.trim()) {
        alert('请填写房间名称')
        return
    }
    const fd = new FormData()
    fd.append('name', form.value.name.trim())
    fd.append('topic', form.value.topic)
    fd.append('model_name', form.value.model_name)
    fd.append('participants', JSON.stringify(form.value.participants))

    const res = await api.post('/api/multi-agent/rooms/', fd)
    if (res.data.result === 'success') {
        showCreate.value = false
        form.value = {name: '', topic: '', model_name: 'deepseek-v4.1-flash', participants: []}
        router.push({name: 'multi-agent-room', params: {room_id: res.data.room.id}})
    } else {
        alert(res.data.result)
    }
}

async function deleteRoom(room) {
    if (!confirm(`确定要删除房间《${room.name}》吗？`)) return
    const res = await api.delete(`/api/multi-agent/rooms/${room.id}/`)
    if (res.data.result === 'success') {
        rooms.value = rooms.value.filter(r => r.id !== room.id)
    } else {
        alert(res.data.result)
    }
}

onMounted(async () => {
    await loadRooms()
    await loadCharacters()
})
</script>

<template>
  <div class="p-4 lg:p-8 max-w-5xl mx-auto w-full">
    <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
      <div class="flex items-center gap-2">
        <AgentChatIcon />
        <h1 class="text-2xl font-bold">多智能体讨论</h1>
      </div>
      <button class="btn btn-primary" @click="showCreate = !showCreate">
        {{ showCreate ? '取消' : '新建讨论房间' }}
      </button>
    </div>

    <p class="text-sm opacity-60 mb-6">
      创建多个 AI 角色，让它们就同一个话题轮流发言、互相回应。需要先在创作页创建角色。
    </p>

    <!-- 新建表单 -->
    <div v-if="showCreate" class="card bg-base-100 shadow-sm mb-6">
      <div class="card-body space-y-3">
        <h2 class="card-title text-lg">新建讨论房间</h2>

        <div class="grid gap-3 sm:grid-cols-2">
          <input v-model="form.name" type="text" placeholder="房间名称" class="input input-bordered input-sm w-full" />
          <input v-model="form.topic" type="text" placeholder="讨论主题（可选）" class="input input-bordered input-sm w-full" />
        </div>

        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">参与者</span>
          <button class="btn btn-xs" @click="addParticipant">添加智能体</button>
        </div>

        <div v-if="form.participants.length === 0" class="text-sm opacity-50 py-2">
          还没添加智能体。至少添加一个才能开始讨论。
        </div>

        <div
            v-for="(p, i) in form.participants"
            :key="i"
            class="flex flex-wrap items-center gap-2 bg-base-200 rounded-lg p-2"
        >
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
          <input v-model="p.system_prompt" type="text" placeholder="性格设定（可选）" class="input input-xs flex-1 min-w-40" />
          <button class="btn btn-ghost btn-xs text-error" @click="removeParticipant(i)">移除</button>
        </div>

        <button class="btn btn-primary btn-sm self-start" @click="createRoom">创建并进入</button>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else-if="rooms.length === 0" class="text-center py-20 opacity-60">
      还没有讨论房间，点上方「新建讨论房间」创建一个
    </div>

    <div v-else class="grid gap-4 sm:grid-cols-2">
      <div v-for="room in rooms" :key="room.id" class="card bg-base-100 shadow-sm hover:shadow-lg transition-shadow">
        <div class="card-body">
          <div class="flex items-start justify-between gap-2">
            <h3 class="card-title text-base">{{ room.name }}</h3>
            <button class="btn btn-ghost btn-xs text-error shrink-0" @click="deleteRoom(room)">
              删除
            </button>
          </div>
          <p class="text-sm opacity-60 line-clamp-2">{{ room.topic || '自由讨论' }}</p>

          <div class="flex flex-wrap gap-1 mt-2">
            <span class="badge badge-sm badge-outline">{{ FLOW_LABELS[room.flow_mode] || room.flow_mode }}</span>
            <span class="badge badge-sm badge-outline">{{ room.participants.length }} 个智能体</span>
          </div>

          <div class="flex flex-wrap gap-1 mt-2">
            <span
                v-for="p in room.participants"
                :key="p.id"
                class="badge badge-sm badge-ghost"
            >{{ p.display_name }}</span>
          </div>

          <button
              class="btn btn-primary btn-sm mt-3"
              @click="router.push({name: 'multi-agent-room', params: {room_id: room.id}})"
          >
            进入讨论
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>
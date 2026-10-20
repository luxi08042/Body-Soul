/**
 * 业务接口封装。
 *
 * 页面里重复的请求逻辑集中到这里，避免每个页面各写一遍参数拼装和错误处理。
 */
import api from "@/js/http/api.js";

/**
 * 拉取某个用户的角色列表。
 *
 * @param {number} userId 用户 id
 * @param {number} itemsCount 偏移量（分页用），0 表示从头取
 * @returns {Promise<Array>} 角色数组，失败时返回空数组
 */
export async function fetchCharacters(userId, itemsCount = 0) {
  try {
    const res = await api.get('/api/create/character/get_list/', {
      params: {user_id: userId, items_count: itemsCount},
    })
    if (res.data.result !== 'success') return []
    return res.data.characters || []
  } catch (e) {
    console.error('获取角色列表失败', e)
    return []
  }
}

/**
 * 拉取音色列表。
 *
 * @returns {Promise<Array>} 音色数组（含 used_count / deletable），失败时返回空数组
 */
export async function fetchVoices() {
  try {
    const res = await api.get('/api/create/character/voice/get_list/')
    if (res.data.result !== 'success') return []
    return res.data.voices || []
  } catch (e) {
    console.error('获取音色列表失败', e)
    return []
  }
}

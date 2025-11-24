import axios, { AxiosInstance } from 'axios'

let accessToken: string | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

export function getAccessToken() {
  return accessToken
}

const api: AxiosInstance = axios.create({
  baseURL: '/',
  withCredentials: true, // allow cookies for refresh token
})

// attach access token
api.interceptors.request.use((config) => {
  if (!config.headers) config.headers = {}
  if (accessToken) {
    config.headers['Authorization'] = `Bearer ${accessToken}`
  }
  return config
})

let isRefreshing = false
let refreshQueue: Array<(token: string | null) => void> = []

async function refreshToken(): Promise<string | null> {
  try {
    const resp = await axios.post('/api/auth/refresh', {}, { withCredentials: true })
    const newToken = resp.data?.access_token
    setAccessToken(newToken)
    return newToken
  } catch (e) {
    setAccessToken(null)
    return null
  }
}

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (err.response && err.response.status === 401 && !original._retry) {
      original._retry = true
      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push((token) => {
            if (token) {
              original.headers['Authorization'] = `Bearer ${token}`
            }
            resolve(axios(original))
          })
        })
      }

      isRefreshing = true
      const token = await refreshToken()
      isRefreshing = false
      refreshQueue.forEach(cb => cb(token))
      refreshQueue = []

      if (token) {
        original.headers['Authorization'] = `Bearer ${token}`
        return axios(original)
      }
    }

    return Promise.reject(err)
  }
)

export { api }

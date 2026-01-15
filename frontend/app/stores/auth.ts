// frontend/stores/auth.ts
import { defineStore } from 'pinia'
import { useRuntimeConfig, navigateTo } from 'nuxt/app'
import { $fetch } from 'ofetch'

interface User {
  id: number
  email: string
  credit: number
  key: string
}

interface AuthState {
  user: User | null
  token: string | null
}

const isClient = () => typeof window !== 'undefined'

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: null,
  }),

  actions: {
    setToken(token: string, remember: boolean = false) {
      this.token = token
      if (isClient()) {
        if (remember) {
          // Ghi nhớ đăng nhập - lưu vào localStorage (5 ngày)
        localStorage.setItem('auth_token', token)
          sessionStorage.removeItem('auth_token') // Xóa session token nếu có
        } else {
          // Không ghi nhớ - lưu vào sessionStorage (1 ngày, mất khi refresh)
          sessionStorage.setItem('auth_token', token)
          localStorage.removeItem('auth_token') // Xóa local token nếu có
        }
      }
    },

    async fetchUser() {
      if (!this.token) return

      const config = useRuntimeConfig()

      try {
        const res = await $fetch<User>(
          `${config.public.apiBase}/user/me`,
          {
            headers: {
              Authorization: this.token,
            },
          }
        )
        this.user = res
      } catch {
        this.logout()
      }
    },

    logout() {
      this.user = null
      this.token = null

      if (isClient()) {
        localStorage.removeItem('auth_token')
        sessionStorage.removeItem('auth_token')
        navigateTo('/')
      }
    },

    initialize() {
      if (!isClient()) return

      // Ưu tiên localStorage (remember me), sau đó mới đến sessionStorage
      const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
      if (token) {
        this.token = token
        this.fetchUser()
      }
    },
  },
})

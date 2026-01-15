<template>
  <header class="header">
    <div class="container header-container">
      <div class="logo">
        <NuxtLink to="/" style="text-decoration: none; color: inherit;">
          NanoAI<span class="highlight">.</span>
        </NuxtLink>
      </div>

      <nav class="navbar">
        <NuxtLink to="/" class="nav-link">Trang chủ</NuxtLink>
        <NuxtLink to="/" class="nav-link">API FLOW</NuxtLink>
        <NuxtLink to="/" class="nav-link">Gói cước</NuxtLink>
        <NuxtLink to="/" class="nav-link">Tài liệu</NuxtLink>
      </nav>

      <div class="header-actions">
        <button class="lang-switch">VI ▾</button>
        <template v-if="auth.user">
          <div class="user-avatar">
            <div class="avatar-circle">
              {{ auth.user?.email?.charAt(0).toUpperCase() || "U" }}
            </div>
            <div class="user-menu">
              <div class="user-info">
                <div class="user-name">{{ auth.user?.email }}</div>
                <div class="user-role">User</div>
              </div>
              <NuxtLink
                to="/dashboard"
                style="
                  display: block;
                  text-align: center;
                  margin-bottom: 10px;
                  text-decoration: none;
                  background: rgba(255, 255, 255, 0.1);
                  border: 1px solid rgba(0, 210, 255, 0.5);
                  color: #00d2ff;
                  padding: 8px 16px;
                  border-radius: 6px;
                  font-size: 0.9rem;
                  cursor: pointer;
                  transition: all 0.3s ease;
                "
              >
                Thông tin
              </NuxtLink>
              <button class="btn-logout" @click="handleLogout">
                Đăng xuất
              </button>
            </div>
          </div>
        </template>
        <template v-else>
          <button
            class="btn-login"
            @click="$emit('open-login')"
            style="text-decoration: none; background: linear-gradient(90deg, #b06ab3, #4568dc); color: white; padding: 8px 20px; border-radius: 6px; transition: all 0.3s ease; border: none; cursor: pointer;"
          >
            Đăng nhập
          </button>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useAuthStore } from "~/stores/auth";

const auth = useAuthStore();

const handleLogout = () => {
  auth.logout();
};
</script>


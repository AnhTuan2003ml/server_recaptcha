<template>
  <div>
    <header class="header">
      <div class="container header-container">
        <div class="logo">
          <NuxtLink to="/" style="text-decoration: none; color: inherit">
            NanoAI<span class="highlight">.</span>
          </NuxtLink>
        </div>

        <nav class="navbar">
          <a
            href="#"
            class="nav-link"
            :class="{ active: currentView === 'home' }"
            @click.prevent="currentView = 'home'"
            >Trang chủ</a
          >
          <a
            href="#"
            class="nav-link"
            :class="{ active: currentView === 'apiflow' }"
            @click.prevent="currentView = 'apiflow'"
            >API FLOW</a
          >
          <a
            href="#"
            class="nav-link"
            :class="{ active: currentView === 'pricing' }"
            @click.prevent="currentView = 'pricing'"
            >Gói cước</a
          >
          <a
            href="#"
            class="nav-link"
            :class="{ active: currentView === 'docs' }"
            @click.prevent="currentView = 'docs'"
            >Tài liệu</a
          >
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
                    cursor: pointer;
                    transition: all 0.3s ease;
                    padding: 4px 16px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 600;
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
              @click="showLoginModal = true"
              style="text-decoration: none"
            >
              Đăng nhập
            </button>
          </template>
        </div>
      </div>
    </header>

    <main id="main-content">
      <!-- View Home (Hero Section) -->
      <section
        v-if="currentView === 'home'"
        id="view-home"
        class="view-section"
      >
        <div class="hero-bg">
          <div class="container hero-content">
            <h1>Chào mừng đến với NanoAI.pics</h1>
            <p class="hero-desc">
              Hệ sinh thái AI tiên tiến cung cấp các giải pháp tự động hóa thông
              minh với Captcha Solver, Video Generation và Image Generation APIs
            </p>

            <div class="stats-grid">
              <div class="stat-item">
                <h3>99.9%</h3>
                <p>Tỷ lệ thành công</p>
              </div>
              <div class="stat-item">
                <h3>24/7</h3>
                <p>Hỗ trợ liên tục</p>
              </div>
              <div class="stat-item">
                <h3>10K+</h3>
                <p>Người dùng tin dùng</p>
              </div>
            </div>

            <div class="hero-buttons">
              <button class="btn-primary" @click="currentView = 'apiflow'">
                Khám phá API
              </button>
              <button class="btn-secondary" @click="currentView = 'docs'">
                Xem tài liệu
              </button>
            </div>
          </div>
        </div>

        <div class="container services-preview">
          <h2>Dịch vụ của chúng tôi</h2>
          <p>
            Các giải pháp AI tiên tiến giúp tự động hóa quy trình làm việc của
            bạn
          </p>
        </div>
      </section>

      <!-- View API Flow -->
      <section
        v-if="currentView === 'apiflow'"
        id="view-apiflow"
        class="view-section"
      >
        <div class="container">
          <div class="api-header-center">
            <h2>API <span class="text-yellow">Console</span></h2>
            <p>
              Tài liệu tích hợp và công cụ kiểm thử trực tiếp cho Developer.
            </p>
          </div>

          <div class="api-config-area">
            <div class="config-box">
              <span class="label-tag">BASE URL</span>
              <span class="config-value url-text">{{
                config.public.apiBase
              }}</span>
            </div>

            <div class="config-box">
              <span class="label-tag">YOUR TOKEN</span>
              <div class="token-display">
                <span class="lock-icon">🔒</span>
                <span class="config-value">{{
                  auth.token
                    ? auth.token.substring(0, 20) + "..."
                    : "Chưa đăng nhập"
                }}</span>
                <span v-if="auth.token" class="status-dot online"></span>
              </div>
            </div>
          </div>

          <div class="endpoint-list">
            <div
              v-for="(endpoint, index) in endpoints"
              :key="index"
              class="endpoint-item"
              :class="{ active: activeEndpoint === index }"
            >
              <div class="endpoint-head" @click="toggleEndpoint(index)">
                <div
                  class="method-badge"
                  :class="endpoint.method.toLowerCase()"
                >
                  {{ endpoint.method }}
                </div>
                <div class="endpoint-path">{{ endpoint.path }}</div>
                <div class="endpoint-desc">{{ endpoint.description }}</div>
                <div class="endpoint-arrow">▼</div>
              </div>
              <div class="endpoint-body">
                <div class="code-block">
                  <pre>{{ JSON.stringify(endpoint.example, null, 2) }}</pre>
                </div>
                <button class="btn-try" @click="tryEndpoint(endpoint)">
                  Try it out
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- View Pricing -->
      <section
        v-if="currentView === 'pricing'"
        id="view-pricing"
        class="view-section"
      >
        <div class="container" style="text-align: center">
          <h2 style="font-size: 36px; margin-bottom: 10px">
            Bảng giá Veo3 Solver
          </h2>
          <p style="color: #cbd5e1; margin-bottom: 40px">
            Giải pháp vượt Captcha tự động, tốc độ cao và chi phí tối ưu nhất.
          </p>

          <div class="pricing-grid">
            <div class="price-card">
              <h3 class="plan-title">BẮT ĐẦU</h3>
              <h2 class="plan-name">Miễn phí</h2>
              <div class="price">
                0đ
                <span style="font-size: 16px; color: #cbd5e1">/trọn đời</span>
              </div>
              <ul>
                <li>🎁 Tặng 100 Captcha</li>
                <li>✅ Full tính năng API</li>
                <li>📩 Nhắn tin Page: KM [ID]</li>
                <li>👉 Gửi: NanoAI Page</li>
                <li>🔑 Xem ID tài khoản của bạn lại</li>
              </ul>
              <button
                class="btn-secondary"
                style="width: 100%; margin-top: 20px"
              >
                Nhận ngay
              </button>
            </div>

            <div class="price-card highlight-card">
              <span class="label-highlight">KHUYÊN DÙNG</span>
              <h3 class="plan-title" style="color: #00d2ff">TIÊU CHUẨN</h3>
              <h2 class="plan-name">Tiêu chuẩn</h2>
              <div class="price" style="color: #00d2ff">
                30đ
                <span style="font-size: 16px; color: #cbd5e1">/request</span>
              </div>

              <div
                style="
                  background: rgba(0, 210, 255, 0.1);
                  padding: 10px;
                  border-radius: 6px;
                  margin-bottom: 20px;
                  font-weight: bold;
                  color: #00d2ff;
                "
              >
                ⚡ Nạp 1tr nhận thêm 50k
              </div>

              <ul>
                <li style="color: white">⚡ Ưu tiên xử lý siêu tốc</li>
                <li style="color: white">✅ Đa luồng không giới hạn</li>
                <li style="color: white">🛠️ Hỗ trợ kỹ thuật 24/7</li>
                <li style="color: white">⚠️ Không Refund vui lòng cân nhắc</li>
              </ul>
              <button
                class="btn-primary"
                @click="handleDepositClick"
                style="
                  width: 100%;
                  margin-top: 20px;
                  background: linear-gradient(90deg, #00d2ff, #007bff);
                "
              >
                Nạp tiền ngay
              </button>
            </div>

            <div class="price-card">
              <h3 class="plan-title">ƯU TIÊN</h3>
              <h2 class="plan-name">Doanh nghiệp</h2>
              <div class="price" style="font-size: 24px">Thỏa thuận</div>
              <ul>
                <li>✔️ Giá đại lý cực tốt</li>
                <li>✔️ Server riêng (Private)</li>
              </ul>
              <button
                class="btn-secondary"
                style="width: 100%; margin-top: 65px"
              >
                Liên hệ Admin
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- View Docs -->
      <section
        v-if="currentView === 'docs'"
        id="view-docs"
        class="view-section"
      >
        <div class="container" style="text-align: center">
          <h2 style="font-size: 36px; margin-bottom: 10px">Tài Liệu</h2>
          <p style="color: #cbd5e1; margin-bottom: 40px">
            Tài liệu hướng dẫn sử dụng API và các tính năng của hệ thống.
          </p>
        </div>
      </section>
    </main>

    <!-- Login Modal -->
    <LoginModal
      v-model="showLoginModal"
      @switch-to-register="switchToRegister"
    />

    <!-- Register Modal -->
    <RegisterModal
      v-model="showRegisterModal"
      @switch-to-login="switchToLogin"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useAuthStore } from "~/stores/auth";
import { useRouter } from "vue-router";

const config = useRuntimeConfig();
const auth = useAuthStore();
const router = useRouter();

// Navigation state
const currentView = ref("home");
const activeEndpoint = ref(null);

// Modal state
const showLoginModal = ref(false);
const showRegisterModal = ref(false);

const switchToRegister = () => {
  showLoginModal.value = false;
  showRegisterModal.value = true;
};

const switchToLogin = () => {
  showRegisterModal.value = false;
  showLoginModal.value = true;
};

// API endpoints data
const endpoints = ref([
  {
    method: "GET",
    path: "/user/me",
    description: "Lấy thông tin user hiện tại",
    example: { id: 1, email: "user@example.com", credit: 1000000 },
  },
  {
    method: "POST",
    path: "/payment/qr",
    description: "Tạo QR code thanh toán",
    example: { success: true, trans_id: "userkey123AB", qr_url: "https://..." },
  },
  {
    method: "GET",
    path: "/payment/history",
    description: "Lấy lịch sử giao dịch",
    example: { success: true, transactions: [] },
  },
]);

const toggleEndpoint = (index) => {
  activeEndpoint.value = activeEndpoint.value === index ? null : index;
};

const tryEndpoint = async (endpoint) => {
  // TODO: Implement API call
  console.log("Try endpoint:", endpoint);
};

const handleDepositClick = () => {
  if (auth.token) {
    // Nếu đã đăng nhập, chuyển đến dashboard
    router.push("/dashboard");
  } else {
    // Nếu chưa đăng nhập, mở modal login
    showLoginModal.value = true;
  }
};

const handleLogout = () => {
  auth.logout();
};

onMounted(() => {
  // Không redirect về login nữa, chỉ initialize auth
  auth.initialize();
  if (auth.token) {
    auth.fetchUser();
  }
});
</script>

<style>
/* Import Google Font */
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap");
</style>

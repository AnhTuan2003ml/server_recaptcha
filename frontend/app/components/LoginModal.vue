<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="modal-overlay-auth"
      @click="handleOverlayClick"
    >
      <div class="modal-container-auth">
        <div class="modal-card-auth">
          <button
            class="modal-close-btn"
            @click="$emit('update:modelValue', false)"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
          <h1 class="title">Đăng Nhập</h1>

          <div v-if="step === 1" class="form-group">
            <label>Email</label>
            <input
              v-model="email"
              type="email"
              placeholder="user@example.com"
              @keyup.enter="loginWithPassword"
            />
            <label>Mật khẩu</label>
            <div class="password-wrapper">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Nhập mật khẩu"
                @keyup.enter="loginWithPassword"
              />
              <button
                type="button"
                class="eye-btn"
                @click="showPassword = !showPassword"
              >
                <svg
                  v-if="!showPassword"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
                <svg
                  v-else
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
                  ></path>
                  <line x1="1" y1="1" x2="23" y2="23"></line>
                </svg>
              </button>
            </div>
            <div class="remember-section">
              <label class="checkbox-label">
                <input type="checkbox" v-model="rememberMe" />
                <span>Ghi nhớ đăng nhập</span>
              </label>
              <button class="btn-forgot" @click="showForgotPassword = true">
                Quên mật khẩu?
              </button>
            </div>
            <button
              class="btn-success"
              @click="loginWithPassword"
              :disabled="loading || !password"
            >
              {{ loading ? "Đang đăng nhập..." : "Đăng nhập" }}
            </button>
            <div class="link-section">
              <span>Hoặc đăng nhập bằng OTP?</span>
              <button class="btn-link" @click="requestOtp">Gửi mã OTP</button>
            </div>
            <div class="link-section">
              <span>Chưa có tài khoản?</span>
              <button class="link" @click="switchToRegister">Đăng ký</button>
            </div>
          </div>

          <div v-else class="form-group">
            <p class="info-text">
              Đã gửi mã OTP tới <b>{{ email }}</b>
            </p>

            <label>Mã OTP</label>
            <input
              v-model="otp"
              type="text"
              class="otp-input"
              placeholder="123456"
              maxlength="6"
              @keyup.enter="verifyOtp"
            />

            <button class="btn-success" @click="verifyOtp" :disabled="loading">
              {{ loading ? "Đang xử lý..." : "Đăng nhập bằng OTP" }}
            </button>

            <button class="btn-link" @click="step = 1">
              Quay lại đăng nhập bằng mật khẩu
            </button>
          </div>

          <p v-if="error" class="error-msg">{{ error }}</p>

          <!-- Modal Quên mật khẩu -->
          <div
            v-if="showForgotPassword"
            class="modal-overlay-inner"
            @click="showForgotPassword = false"
          >
            <div class="modal-content-inner" @click.stop>
              <h2>Quên Mật Khẩu</h2>
              <div class="form-group">
                <label>Email</label>
                <input
                  v-model="forgotEmail"
                  type="email"
                  placeholder="user@example.com"
                  @keyup.enter="resetPassword"
                />
              </div>
              <div class="modal-actions">
                <button
                  class="btn-secondary"
                  @click="showForgotPassword = false"
                >
                  Hủy
                </button>
                <button
                  class="btn-primary"
                  @click="resetPassword"
                  :disabled="loading || !forgotEmail"
                >
                  {{ loading ? "Đang gửi..." : "Gửi mật khẩu mới" }}
                </button>
              </div>
              <p v-if="successMsg" class="success-msg">{{ successMsg }}</p>
              <p v-if="forgotError" class="error-msg">{{ forgotError }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from "vue";
import { useAuthStore } from "~/stores/auth";
import { useRouter } from "vue-router";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:modelValue", "switch-to-register"]);

const config = useRuntimeConfig();
const auth = useAuthStore();
const router = useRouter();

const step = ref(1);
const email = ref("");
const password = ref("");
const otp = ref("");
const rememberMe = ref(false);
const loading = ref(false);
const error = ref("");
const showPassword = ref(false);
const showForgotPassword = ref(false);
const forgotEmail = ref("");
const forgotError = ref("");
const successMsg = ref("");

const switchToRegister = () => {
  emit("update:modelValue", false);
  emit("switch-to-register");
};

const handleOverlayClick = (event) => {
  const target = event.target;
  // Nếu click không nằm trong khối modal-card-auth thì đóng modal
  if (!(target instanceof HTMLElement)) return;
  if (!target.closest(".modal-card-auth")) {
    emit("update:modelValue", false);
  }
};

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      // Reset form when modal opens
      step.value = 1;
      email.value = "";
      password.value = "";
      otp.value = "";
      error.value = "";
      showPassword.value = false;
      showForgotPassword.value = false;
      forgotEmail.value = "";
      forgotError.value = "";
      successMsg.value = "";
    }
  }
);

const loginWithPassword = async () => {
  if (!email.value || !password.value) {
    error.value = "Vui lòng nhập đầy đủ thông tin";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    const res = await $fetch(`${config.public.apiBase}/auth/login`, {
      method: "POST",
      body: {
        email: email.value,
        password: password.value,
        remember: rememberMe.value,
      },
    });

    if (res.success) {
      auth.setToken(res.token, rememberMe.value);
      await auth.fetchUser();
      emit("update:modelValue", false);
      router.push("/dashboard");
    }
  } catch (err) {
    if (err.data?.error) {
      error.value = err.data.error;
    } else {
      error.value = "Email hoặc mật khẩu không đúng!";
    }
  } finally {
    loading.value = false;
  }
};

const requestOtp = async () => {
  if (!email.value) {
    error.value = "Vui lòng nhập email";
    return;
  }

  step.value = 2;
  error.value = "";
  loading.value = true;

  try {
    await $fetch(`${config.public.apiBase}/auth/login/otp`, {
      method: "POST",
      body: { email: email.value },
    });
  } catch (err) {
    step.value = 1;
    if (err.data?.error) {
      error.value = err.data.error;
    } else {
      error.value = "Lỗi kết nối Backend!";
    }
  } finally {
    loading.value = false;
  }
};

const verifyOtp = async () => {
  if (!otp.value) {
    error.value = "Vui lòng nhập mã OTP";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    const res = await $fetch(`${config.public.apiBase}/auth/login`, {
      method: "POST",
      body: { email: email.value, otp: otp.value },
    });

    if (res.success) {
      auth.setToken(res.token, res.remember || false);
      await auth.fetchUser();
      emit("update:modelValue", false);
      router.push("/dashboard");
    }
  } catch (err) {
    if (err.data?.error) {
      error.value = err.data.error;
    } else {
      error.value = "Mã OTP không đúng!";
    }
  } finally {
    loading.value = false;
  }
};

const resetPassword = async () => {
  if (!forgotEmail.value) {
    forgotError.value = "Vui lòng nhập email";
    return;
  }

  loading.value = true;
  forgotError.value = "";
  successMsg.value = "";

  try {
    await $fetch(`${config.public.apiBase}/auth/forgot-password`, {
      method: "POST",
      body: { email: forgotEmail.value },
    });

    successMsg.value = "Mật khẩu mới đã được gửi đến email của bạn!";
    forgotEmail.value = "";
    setTimeout(() => {
      showForgotPassword.value = false;
      successMsg.value = "";
      forgotError.value = "";
    }, 1000);
  } catch (err) {
    if (err.data?.error) {
      forgotError.value = err.data.error;
    } else {
      forgotError.value = "Lỗi kết nối Backend!";
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.modal-overlay-auth {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.52);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
}

.modal-container-auth {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.modal-card-auth {
  background: #1e293b;
  padding: 2.5rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  width: 100%;
  max-width: 500px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
}

.modal-close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  padding: 0;
  z-index: 10;
}

.modal-close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #ffffff;
  transform: scale(1.05);
}

.modal-close-btn svg {
  width: 18px;
  height: 18px;
}

.title {
  text-align: center;
  color: #ffffff;
  margin-bottom: 1.5rem;
  font-size: 1.8rem;
  font-weight: 700;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

label {
  font-weight: 600;
  font-size: 0.9rem;
  color: #cbd5e1;
  margin: 0px;
}

input {
  padding: 12px 15px;
  border: 1px solid #475569;
  border-radius: 6px;
  font-size: 1rem;
  width: 100%;
  box-sizing: border-box;
  background: #0f172a;
  color: #ffffff;
  transition: border-color 0.3s;
}

input::placeholder {
  color: #64748b;
}

input:focus {
  outline: none;
  border-color: #00d2ff;
  box-shadow: 0 0 0 2px rgba(0, 210, 255, 0.2);
}

.password-wrapper {
  position: relative;
}

.password-wrapper input {
  padding-right: 45px;
}

.eye-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  line-height: 1;
  color: #888;
  display: flex;
  align-items: center;
  justify-content: center;
}

.eye-btn:hover {
  color: #00d2ff;
}

.eye-btn svg {
  width: 20px;
  height: 20px;
}

.remember-section {
  display: flex;
  justify-content: space-between;
  align-items: center;

  margin-bottom: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: normal;
  font-size: 0.9rem;
  cursor: pointer;
  margin: 0;
  color: #cbd5e1;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  margin: 0;
  cursor: pointer;
}

.btn-forgot {
  background: none;
  border: none;
  color: #00d2ff;
  font-size: 0.9rem;
  cursor: pointer;
  padding: 0;
  font-weight: normal;
}

.btn-forgot:hover {
  text-decoration: underline;
  color: #00f2ea;
}

.otp-input {
  text-align: center;
  letter-spacing: 4px;
  font-size: 1.2rem;
}

.modal-overlay-inner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10001;
}

.modal-content-inner {
  background: #1e293b;
  padding: 2rem;
  border-radius: 12px;
  max-width: 400px;
  width: 90%;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-content-inner h2 {
  margin-top: 0;
  color: #ffffff;
}

.modal-content-inner label {
  color: #cbd5e1;
}

.modal-content-inner input {
  background: #0f172a;
  border: 1px solid #475569;
  color: #ffffff;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  flex: 1;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

.success-msg {
  color: #4ade80;
  text-align: center;
  margin-top: 1rem;
  font-size: 0.9rem;
  background: rgba(39, 174, 96, 0.2);
  border: 1px solid rgba(39, 174, 96, 0.5);
  padding: 0.75rem;
  border-radius: 6px;
}

button {
  padding: 12px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(90deg, #00c6ff, #0072ff);
  color: white;
  flex: 1;
  box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4);
}
.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 114, 255, 0.6);
}

.btn-success {
  background: linear-gradient(90deg, #00c6ff, #0072ff);
  color: white;
  width: 100%;
  box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4);
}
.btn-success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 114, 255, 0.6);
}

.btn-link {
  background: none;
  color: #00d2ff;
  font-size: 0.9rem;
  font-weight: normal;
  padding: 8px;
}
.btn-link:hover {
  text-decoration: underline;
  color: #00f2ea;
}

.link-section {
  text-align: center;
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #cbd5e1;
}

.link {
  color: #00d2ff;
  text-decoration: none;
  margin-left: 0.5rem;
  font-weight: 600;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}
.link:hover {
  text-decoration: underline;
  color: #00f2ea;
}

.info-text {
  text-align: center;
  color: #cbd5e1;
  margin: 0;
}

.error-msg {
  color: #f87171;
  text-align: center;
  margin-top: 1rem;
  font-size: 0.9rem;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.5);
  padding: 0.75rem;
  border-radius: 6px;
}
</style>

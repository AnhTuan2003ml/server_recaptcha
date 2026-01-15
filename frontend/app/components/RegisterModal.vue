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
          <h1 class="title">Đăng Ký</h1>

          <div v-if="step === 1" class="form-group">
            <label>Email</label>
            <input
              v-model="email"
              type="email"
              placeholder="user@example.com"
              @keyup.enter="requestOtp"
            />
            <label>Mật khẩu</label>
            <div class="password-wrapper">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Tối thiểu 6 ký tự"
                @keyup.enter="requestOtp"
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
            <label>Xác nhận mật khẩu</label>
            <div class="password-wrapper">
              <input
                v-model="confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                placeholder="Nhập lại mật khẩu"
                @keyup.enter="requestOtp"
              />
              <button
                type="button"
                class="eye-btn"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                <svg
                  v-if="!showConfirmPassword"
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
            <button
              class="btn-primary"
              @click="requestOtp"
              :disabled="
                sendingOtp ||
                !password ||
                password.length < 6 ||
                password !== confirmPassword
              "
            >
              {{ sendingOtp ? "Đang gửi..." : "Gửi mã OTP" }}
            </button>
            <div class="link-section">
              <span>Đã có tài khoản?</span>
              <button class="link" @click="switchToLogin">Đăng nhập</button>
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
              {{ loading ? "Đang xử lý..." : "Xác nhận đăng ký" }}
            </button>

            <button class="btn-link" @click="step = 1">
              Quay lại nhập Email
            </button>
          </div>

          <p v-if="error" class="error-msg">{{ error }}</p>
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

const emit = defineEmits(["update:modelValue", "switch-to-login"]);

const config = useRuntimeConfig();
const auth = useAuthStore();
const router = useRouter();

const step = ref(1);
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const otp = ref("");
const loading = ref(false);
const sendingOtp = ref(false);
const error = ref("");
const showPassword = ref(false);
const showConfirmPassword = ref(false);

const switchToLogin = () => {
  emit("update:modelValue", false);
  emit("switch-to-login");
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
      confirmPassword.value = "";
      otp.value = "";
      error.value = "";
      showPassword.value = false;
      showConfirmPassword.value = false;
    }
  }
);

const requestOtp = async () => {
  if (!email.value) {
    error.value = "Vui lòng nhập email";
    return;
  }

  if (!password.value) {
    error.value = "Vui lòng nhập mật khẩu";
    return;
  }

  if (password.value.length < 6) {
    error.value = "Mật khẩu phải có ít nhất 6 ký tự";
    return;
  }

  if (password.value !== confirmPassword.value) {
    error.value = "Mật khẩu xác nhận không khớp";
    return;
  }

  error.value = "";
  sendingOtp.value = true;

  try {
    await $fetch(`${config.public.apiBase}/auth/register`, {
      method: "POST",
      body: {
        email: email.value,
        password: password.value,
      },
    });

    // Chỉ chuyển sang step 2 khi API call thành công
    step.value = 2;
  } catch (err) {
    if (err.data?.error) {
      error.value = err.data.error;
    } else {
      error.value = "Lỗi kết nối Backend!";
    }
  } finally {
    sendingOtp.value = false;
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
    const res = await $fetch(`${config.public.apiBase}/auth/register/verify`, {
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

.otp-input {
  text-align: center;
  letter-spacing: 4px;
  font-size: 1.2rem;
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
  width: 100%;
  box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4);
  margin-top: 0.5rem;
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

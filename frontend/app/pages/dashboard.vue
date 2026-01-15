<template>
  <div>
    <AppHeader />

    <div class="dashboard-container">
      <div class="balance-card">
        <p class="greeting">Xin chào, {{ auth.user?.email }}</p>

        <div class="credit-display">
          <span>Số điểm hiện có:</span>
          <h1 class="amount">{{ formatCredit(auth.user?.credit || 0) }}</h1>
        </div>

        <!-- API Key Section -->
        <div class="api-key-section">
          <div class="api-key-label">API Key của bạn:</div>
          <div class="api-key-display">
            <input
              type="text"
              :value="auth.user?.key || 'N/A'"
              readonly
              class="api-key-input"
              ref="apiKeyInput"
            />
            <button
              class="btn-copy"
              @click="copyApiKey"
              :disabled="copying"
            >
              {{ copying ? "Đã sao chép!" : "📋 Sao chép" }}
            </button>
            <button
              class="btn-regenerate"
              @click="regenerateApiKey"
              :disabled="regenerating"
            >
              {{ regenerating ? "Đang tạo..." : "🔄 Tạo mới" }}
            </button>
          </div>
          <p class="api-key-note">
            🔐 API Key dùng để gọi các API endpoints. Giữ bí mật key này!
          </p>
        </div>

        <p v-if="topupSuccess" class="success-msg">{{ topupSuccess }}</p>

        <div v-if="deductSuccess" class="deduct-success">
          {{ deductSuccess }}
        </div>
        <div v-if="deductError" class="deduct-error">{{ deductError }}</div>

        <div class="actions">
          <button class="btn-deposit" @click.stop="showDepositModal = true">
            Nạp Tiền (QR)
          </button>
          <button class="btn-history" @click.stop="showHistory = true">
            Lịch sử
          </button>
          <button
            class="btn-deduct"
            @click="deductCredit"
            :disabled="deductingCredit"
          >
            {{ deductingCredit ? "Đang xử lý..." : "🧪 Test Trừ Điểm" }}
          </button>
          <button
            class="btn-change-password"
            @click="showChangePasswordModal = true"
            style="
              background: rgba(255, 255, 255, 0.1);
              border: 1px solid rgba(0, 210, 255, 0.5);
              color: #00d2ff;
              padding: 10px 20px;
              border-radius: 8px;
              cursor: pointer;
              transition: all 0.3s ease;
            "
          >
            Đổi mật khẩu
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Nạp tiền -->
    <div
      v-if="showDepositModal"
      class="modal-overlay"
      @click="showDepositModal = false"
    >
      <div class="modal-content" @click.stop>
        <div v-if="!qrData" class="form-group">
          <label>Số tiền (VND)</label>
          <input
            v-model="depositAmountDisplay"
            type="text"
            placeholder="Nhập số tiền (vd: 1.000.000)"
            @input="handleAmountInput"
            @blur="formatAmount"
          />
        </div>
        <div v-if="qrData && !qrExpired" class="qr-container">
          <p class="qr-info">Quét QR code để thanh toán:</p>
          <div v-if="qrTimeRemaining > 0" class="qr-countdown">
            <span class="countdown-text">QR code hết hạn sau: </span>
            <span class="countdown-time">{{
              formatTimeRemaining(qrTimeRemaining)
            }}</span>
          </div>
          <div v-else class="qr-expired-notice">
            <p class="expired-text">QR code đã hết hạn</p>
          </div>
          <img
            :src="qrData.qr_url"
            alt="QR Code"
            class="qr-image"
            v-if="qrTimeRemaining > 0"
          />
          <p class="qr-memo">Nội dung: {{ qrData.memo }}</p>
          <p class="qr-amount">Số tiền: {{ formatCurrency(depositAmount) }}</p>
        </div>
        <div v-if="qrExpired" class="qr-expired-container">
          <p class="expired-message">⚠️ QR code đã hết hạn (quá 5 phút)</p>
          <p class="expired-hint">Vui lòng tạo QR code mới để tiếp tục</p>
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="closeDepositModal">Đóng</button>
          <button
            v-if="qrData"
            class="btn-test"
            @click="testPayment"
            :disabled="testingPayment"
          >
            {{ testingPayment ? "Đang test..." : "🧪 Test Thanh Toán" }}
          </button>
          <button
            class="btn-primary qr-btn"
            @click="createQR"
            :disabled="loading || !depositAmount || depositAmount < 10000"
          >
            {{
              loading ? "Đang tạo..." : qrData ? "Tạo QR mới" : "Tạo QR Code"
            }}
          </button>
        </div>
        <p v-if="error" class="error-msg">{{ error }}</p>
        <p v-if="testSuccess" class="success-msg">{{ testSuccess }}</p>
      </div>
    </div>

    <!-- Modal Lịch sử thanh toán -->
    <div v-if="showHistory" class="modal-overlay" @click="showHistory = false">
      <div class="modal-content history-modal" @click.stop>
        <h2>Lịch Sử Thanh Toán</h2>
        <div v-if="loadingHistory" class="loading-history">
          Đang tải lịch sử...
        </div>
        <div v-else-if="transactionHistory.length === 0" class="no-history">
          <p>Chưa có giao dịch nào</p>
        </div>
        <div v-else class="history-list">
          <div
            v-for="tx in transactionHistory"
            :key="tx.id"
            class="history-item"
          >
            <div class="history-item-header">
              <span class="history-id">ID: {{ tx.id }}</span>
              <span
                :class="[
                  'history-status',
                  {
                    'status-success': tx.status === 'success',
                    'status-pending': tx.status === 'pending',
                    'status-cancelled': tx.status === 'cancelled',
                  },
                ]"
              >
                {{ getStatusText(tx.status) }}
              </span>
            </div>
            <div class="history-item-body">
              <p class="history-amount">
                Số tiền: {{ formatCurrency(tx.amount) }}
              </p>
              <p class="history-content">Nội dung: {{ tx.content }}</p>
              <p class="history-date">
                Thời gian: {{ formatDate(tx.created_at) }}
              </p>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showHistory = false">
            Đóng
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Đổi mật khẩu -->
    <div
      v-if="showChangePasswordModal"
      class="modal-overlay"
      @click="showChangePasswordModal = false"
    >
      <div class="modal-content" @click.stop>
        <h2>Đặt Lại Mật Khẩu</h2>
        <div class="form-group">
          <label>Mật khẩu cũ</label>
          <div class="password-wrapper">
            <input
              v-model="oldPassword"
              :type="showOldPassword ? 'text' : 'password'"
              placeholder="Nhập mật khẩu cũ"
              @keyup.enter="changePassword"
            />
            <button
              type="button"
              class="eye-btn"
              @click="showOldPassword = !showOldPassword"
            >
              <svg
                v-if="!showOldPassword"
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
        </div>
        <div class="form-group">
          <label>Mật khẩu mới</label>
          <div class="password-wrapper">
            <input
              v-model="newPassword"
              :type="showNewPassword ? 'text' : 'password'"
              placeholder="Tối thiểu 6 ký tự"
              @keyup.enter="changePassword"
            />
            <button
              type="button"
              class="eye-btn"
              @click="showNewPassword = !showNewPassword"
            >
              <svg
                v-if="!showNewPassword"
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
        </div>
        <div class="form-group">
          <label>Xác nhận mật khẩu mới</label>
          <div class="password-wrapper">
            <input
              v-model="confirmNewPassword"
              :type="showConfirmNewPassword ? 'text' : 'password'"
              placeholder="Nhập lại mật khẩu mới"
              @keyup.enter="changePassword"
            />
            <button
              type="button"
              class="eye-btn"
              @click="showConfirmNewPassword = !showConfirmNewPassword"
            >
              <svg
                v-if="!showConfirmNewPassword"
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
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="closeChangePasswordModal">
            Hủy
          </button>
          <button
            class="btn-primary"
            @click="changePassword"
            :disabled="
              loading ||
              !oldPassword ||
              !newPassword ||
              newPassword.length < 6 ||
              newPassword !== confirmNewPassword
            "
          >
            {{ loading ? "Đang xử lý..." : "Đổi mật khẩu" }}
          </button>
        </div>
        <p v-if="changePasswordError" class="error-msg">
          {{ changePasswordError }}
        </p>
        <p v-if="changePasswordSuccess" class="success-msg">
          {{ changePasswordSuccess }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import { useAuthStore } from "~/stores/auth";
import { useRouter } from "vue-router";

const config = useRuntimeConfig();
const auth = useAuthStore();
const router = useRouter();

const showDepositModal = ref(false);
const showHistory = ref(false);
const showChangePasswordModal = ref(false);
const depositAmount = ref(null);
const depositAmountDisplay = ref("");
const qrData = ref(null);
const qrTimeRemaining = ref(0);
const qrExpired = ref(false);
const qrCountdownInterval = ref(null);
const loading = ref(false);
const error = ref("");
const testingPayment = ref(false);
const testSuccess = ref("");
const topupSuccess = ref("");
const deductingCredit = ref(false);
const deductError = ref("");
const deductSuccess = ref("");
const transactionHistory = ref([]);
const loadingHistory = ref(false);

const oldPassword = ref("");
const newPassword = ref("");
const confirmNewPassword = ref("");
const showOldPassword = ref(false);
const showNewPassword = ref(false);
const showConfirmNewPassword = ref(false);
const changePasswordError = ref("");
const changePasswordSuccess = ref("");

// API Key management
const copying = ref(false);
const regenerating = ref(false);
const apiKeyInput = ref(null);

const formatCurrency = (value) => {
  if (!value) return "0 ₫";
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
  }).format(value);
};

const formatCredit = (value) => {
  if (!value) return "0";
  return new Intl.NumberFormat("vi-VN").format(value);
};

const formatTimeRemaining = (seconds) => {
  if (seconds <= 0) return "00:00";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs
    .toString()
    .padStart(2, "0")}`;
};

const startQrCountdown = (expiresInSeconds) => {
  qrTimeRemaining.value = expiresInSeconds;
  qrExpired.value = false;

  if (qrCountdownInterval.value) {
    clearInterval(qrCountdownInterval.value);
  }

  qrCountdownInterval.value = setInterval(() => {
    qrTimeRemaining.value--;

    if (qrTimeRemaining.value <= 0) {
      clearInterval(qrCountdownInterval.value);
      qrCountdownInterval.value = null;
      qrExpired.value = true;
      qrData.value = null;
      error.value =
        "QR code đã hết hạn (quá 5 phút). Vui lòng tạo QR code mới.";
    }
  }, 1000);
};

const stopQrCountdown = () => {
  if (qrCountdownInterval.value) {
    clearInterval(qrCountdownInterval.value);
    qrCountdownInterval.value = null;
  }
  qrTimeRemaining.value = 0;
  qrExpired.value = false;
};

let paymentEventSource = null;

const stopPaymentPolling = () => {
  if (paymentEventSource) {
    paymentEventSource.close();
    paymentEventSource = null;
  }
};

const startPaymentPolling = async () => {
  stopPaymentPolling();

  if (!qrData.value || !qrData.value.trans_id) {
    return;
  }

  try {
    await $fetch(`${config.public.apiBase}/payment/sync-session`, {
      method: "POST",
      headers: {
        Authorization: auth.token,
      },
      credentials: "include",
    });

    paymentEventSource = new EventSource(
      `${config.public.apiBase}/payment/stream?token=${auth.token}`
    );

    paymentEventSource.addEventListener("payment_success", async (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.trans_id === qrData.value?.trans_id) {
          stopPaymentPolling();
          stopQrCountdown();

          topupSuccess.value = `✅ Thanh toán thành công! Đã cộng ${formatCredit(
            data.actual_amount
          )} điểm. Số điểm mới: ${formatCredit(data.new_credit)}`;

          closeDepositModal();

          await auth.fetchUser();

          setTimeout(() => {
            topupSuccess.value = "";
          }, 5000);
        }
      } catch (err) {
        console.error("Error parsing SSE event:", err);
      }
    });

    paymentEventSource.onerror = (error) => {
      // Auto reconnect logic if needed
    };
  } catch (err) {
    console.error("Error setting up SSE connection:", err);
    error.value = "Không thể kết nối SSE. Vui lòng thử lại.";
  }
};

const formatNumber = (value) => {
  if (!value) return "";
  const num = parseFloat(String(value).replace(/\./g, ""));
  if (isNaN(num)) return "";
  return num.toLocaleString("vi-VN");
};

const handleAmountInput = (event) => {
  const value = event.target.value;
  const cleaned = value.replace(/[^\d]/g, "");

  if (cleaned === "") {
    depositAmountDisplay.value = "";
    depositAmount.value = null;
    return;
  }

  const num = parseInt(cleaned);
  depositAmount.value = num;
  depositAmountDisplay.value = num.toLocaleString("vi-VN");
};

const formatAmount = () => {
  if (depositAmount.value) {
    depositAmountDisplay.value = formatNumber(depositAmount.value);
  }
};

const createQR = async () => {
  if (!depositAmount.value || depositAmount.value < 10000) {
    error.value = "Số tiền tối thiểu là 10,000 VND";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    const res = await $fetch(`${config.public.apiBase}/payment/qr`, {
      method: "POST",
      headers: {
        Authorization: auth.token,
      },
      body: {
        amount: depositAmount.value,
      },
    });

    if (res.success) {
      qrData.value = res;
      qrExpired.value = false;
      const expiresIn = res.expires_in_seconds || 300;
      startQrCountdown(expiresIn);
      startPaymentPolling();
      await auth.fetchUser();
    }
  } catch (err) {
    if (err.data?.error) {
      error.value = err.data.error;
    } else {
      error.value = "Lỗi khi tạo QR code!";
    }
  } finally {
    loading.value = false;
  }
};

const closeDepositModal = () => {
  showDepositModal.value = false;
  stopQrCountdown();
  stopPaymentPolling();
  qrData.value = null;
  qrExpired.value = false;
  depositAmount.value = null;
  depositAmountDisplay.value = "";
  error.value = "";
  testSuccess.value = "";
};

const testPayment = async () => {
  if (!qrData.value || !qrData.value.trans_id) {
    error.value = "Không có mã giao dịch để test";
    return;
  }

  if (qrExpired.value || qrTimeRemaining.value <= 0) {
    error.value = "QR code đã hết hạn. Vui lòng tạo QR code mới.";
    return;
  }

  testingPayment.value = true;
  error.value = "";
  testSuccess.value = "";

  try {
    const res = await $fetch(
      `${config.public.apiBase}/payment/test/simulate-payment`,
      {
        method: "POST",
        headers: {
          Authorization: auth.token,
        },
        body: {
          trans_id: qrData.value.trans_id,
        },
      }
    );

    if (res.success) {
      topupSuccess.value = `✅ Test thành công! Đã cộng ${formatCredit(
        res.actual_amount || res.amount
      )} điểm. Số điểm mới: ${formatCredit(res.new_credit)}`;
      stopQrCountdown();
      qrData.value = null;
      closeDepositModal();
      await auth.fetchUser();
      setTimeout(() => {
        topupSuccess.value = "";
      }, 5000);
    }
  } catch (err) {
    if (err.data?.error) {
      error.value = err.data.error;
      if (
        err.data.error.includes("hết hạn") ||
        err.data.error.includes("expired")
      ) {
        qrExpired.value = true;
        stopQrCountdown();
      }
    } else {
      error.value = "Lỗi khi test thanh toán!";
    }
  } finally {
    testingPayment.value = false;
  }
};

const closeChangePasswordModal = () => {
  showChangePasswordModal.value = false;
  oldPassword.value = "";
  newPassword.value = "";
  confirmNewPassword.value = "";
  changePasswordError.value = "";
  changePasswordSuccess.value = "";
};

const changePassword = async () => {
  if (!oldPassword.value) {
    changePasswordError.value = "Vui lòng nhập mật khẩu cũ";
    return;
  }

  if (!newPassword.value) {
    changePasswordError.value = "Vui lòng nhập mật khẩu mới";
    return;
  }

  if (newPassword.value.length < 6) {
    changePasswordError.value = "Mật khẩu mới phải có ít nhất 6 ký tự";
    return;
  }

  if (newPassword.value !== confirmNewPassword.value) {
    changePasswordError.value = "Mật khẩu xác nhận không khớp";
    return;
  }

  loading.value = true;
  changePasswordError.value = "";
  changePasswordSuccess.value = "";

  try {
    const res = await $fetch(`${config.public.apiBase}/auth/change-password`, {
      method: "POST",
      headers: {
        Authorization: auth.token,
      },
      body: {
        old_password: oldPassword.value,
        new_password: newPassword.value,
      },
    });

    if (res.success) {
      changePasswordSuccess.value = "Đổi mật khẩu thành công!";
      setTimeout(() => {
        closeChangePasswordModal();
      }, 2000);
    }
  } catch (err) {
    if (err.data?.error) {
      changePasswordError.value = err.data.error;
    } else {
      changePasswordError.value = "Lỗi khi đổi mật khẩu!";
    }
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  try {
    const date = new Date(dateString);
    return date.toLocaleString("vi-VN", {
      timeZone: "Asia/Ho_Chi_Minh",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return dateString;
  }
};

const getStatusText = (status) => {
  const statusMap = {
    success: "Thành công",
    pending: "Đang chờ",
    cancelled: "Đã hủy",
  };
  return statusMap[status] || status;
};

const loadTransactionHistory = async () => {
  loadingHistory.value = true;
  try {
    const res = await $fetch(`${config.public.apiBase}/payment/history`, {
      method: "GET",
      headers: {
        Authorization: auth.token,
      },
    });

    if (res.success) {
      transactionHistory.value = res.transactions || [];
    }
  } catch (err) {
    console.error("Lỗi khi load lịch sử:", err);
    transactionHistory.value = [];
  } finally {
    loadingHistory.value = false;
  }
};

watch(showHistory, (newVal) => {
  if (newVal) {
    loadTransactionHistory();
  }
});

const deductCredit = async () => {
  deductingCredit.value = true;
  deductError.value = "";
  deductSuccess.value = "";

  try {
    const res = await $fetch(`${config.public.apiBase}/payment/deduct`, {
      method: "POST",
      headers: {
        Authorization: auth.token,
      },
    });

    if (res.success) {
      deductSuccess.value = `✅ Đã trừ ${formatCredit(
        res.cost
      )} điểm thành công! Số điểm còn lại: ${formatCredit(res.new_credit)}`;
      await auth.fetchUser();
      setTimeout(() => {
        deductSuccess.value = "";
      }, 5000);
    }
  } catch (err) {
    if (err.data?.error) {
      deductError.value = err.data.error;
    } else {
      deductError.value = "Lỗi khi trừ điểm!";
    }
    setTimeout(() => {
      deductError.value = "";
    }, 5000);
  } finally {
    deductingCredit.value = false;
  }
};

const copyApiKey = async () => {
  const apiKey = auth.user?.key;
  if (!apiKey) return;

  try {
    await navigator.clipboard.writeText(apiKey);
    copying.value = true;
    setTimeout(() => {
      copying.value = false;
    }, 2000);
  } catch (err) {
    // Fallback for older browsers
    if (apiKeyInput.value) {
      apiKeyInput.value.select();
      document.execCommand('copy');
      copying.value = true;
      setTimeout(() => {
        copying.value = false;
      }, 2000);
    }
  }
};

const regenerateApiKey = async () => {
  if (!confirm("⚠️ Bạn có chắc muốn tạo API Key mới?\n\nAPI Key cũ sẽ không còn hoạt động!")) {
    return;
  }

  regenerating.value = true;

  try {
    const res = await $fetch(`${config.public.apiBase}/user/regenerate-key`, {
      method: "POST",
      headers: {
        Authorization: auth.token,
      },
    });

    if (res.success) {
      await auth.fetchUser(); // Refresh user data
      alert("✅ API Key mới đã được tạo thành công!");
    }
  } catch (err) {
    alert("❌ Lỗi khi tạo API Key mới: " + (err.data?.error || "Lỗi không xác định"));
  } finally {
    regenerating.value = false;
  }
};

onMounted(() => {
  auth.initialize();
  if (!auth.token) {
    router.push("/login");
  } else {
    auth.fetchUser();
  }
});

onBeforeUnmount(() => {
  stopQrCountdown();
  stopPaymentPolling();
});
</script>

<style scoped>
/* API Key Section */
.api-key-section {
  margin-top: 20px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(0, 210, 255, 0.2);
}

.api-key-label {
  font-size: 14px;
  font-weight: 600;
  color: #cbd5e1;
  margin-bottom: 10px;
}

.api-key-display {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}

.api-key-input {
  flex: 1;
  padding: 12px 15px;
  border: 1px solid #475569;
  border-radius: 6px;
  background: #0f172a;
  color: #ffffff;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 1px;
}

.api-key-input:focus {
  outline: none;
  border-color: #00d2ff;
  box-shadow: 0 0 0 2px rgba(0, 210, 255, 0.2);
}

.btn-copy, .btn-regenerate {
  padding: 12px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-copy {
  background: rgba(0, 210, 255, 0.1);
  color: #00d2ff;
  border: 1px solid rgba(0, 210, 255, 0.5);
}

.btn-copy:hover:not(:disabled) {
  background: rgba(0, 210, 255, 0.2);
  transform: translateY(-1px);
}

.btn-copy:disabled {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.5);
}

.btn-regenerate {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.5);
}

.btn-regenerate:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.2);
  transform: translateY(-1px);
}

.btn-regenerate:disabled {
  background: rgba(156, 163, 175, 0.1);
  color: #9ca3af;
  border-color: rgba(156, 163, 175, 0.5);
  cursor: not-allowed;
}

.api-key-note {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
  padding: 8px 0 0 0;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.api-key-note::before {
  content: "ℹ️ ";
  margin-right: 5px;
}

/* Responsive */
@media (max-width: 768px) {
  .api-key-display {
    flex-direction: column;
    gap: 8px;
  }

  .btn-copy, .btn-regenerate {
    width: 100%;
  }
}
</style>

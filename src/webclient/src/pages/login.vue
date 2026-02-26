<template>
  <v-container fluid>
    <v-row justify="center">
      <v-col md="4">
        <v-overlay :model-value="isLoading" class="justify-center align-center">
          <v-progress-circular
            indeterminate
            color="white"
          ></v-progress-circular>
        </v-overlay>
        <v-card class="pa-8 mx-auto">
          <v-card-title class="text-center">Inloggen</v-card-title>
          <v-card-item>
            <v-sheet>
              <v-form @submit.prevent>
                <v-text-field
                  v-model="form_data.username"
                  label="Email"
                  variant="solo"
                  prepend-inner-icon="mdi-email"
                  :rules="[rules.required, rules.username, rules.max]"
                ></v-text-field>
                <v-text-field
                  type="password"
                  v-model="form_data.password"
                  label="Password"
                  variant="solo"
                  prepend-inner-icon="mdi-key"
                  :rules="[rules.required, rules.max]"
                ></v-text-field>
                <v-container>
                  <v-row>
                    <v-text-field
                      v-model="form_data.capchaText"
                      label="Enter verification code"
                      variant="solo"
                      :rules="[rules.required, rules.max]"
                    ></v-text-field
                    ><v-img
                      :src="imageSrc"
                      alt="Verification code"
                      class="mb-4"
                      max-height="60"
                      @click="refreshCaptcha"
                      style="cursor: pointer"
                    >
                    </v-img>
                  </v-row>
                </v-container>
                <v-checkbox
                  v-model="form_data.remember"
                  color="red"
                  label="Remember me 30 days"
                  hide-details
                ></v-checkbox>
                <v-btn type="submit" color="primary" @click="submit" block>
                  <span>Login</span>
                </v-btn>
                <v-alert
                  closable
                  icon="mdi-alert-circle-outline"
                  :text="error_msg"
                  type="error"
                  v-if="error"
                ></v-alert>
              </v-form>
            </v-sheet>
          </v-card-item>
          <v-card-actions>
            <div class="mx-4">
              <v-btn block to="/register">Regist</v-btn>
            </div>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>
    import { ref, reactive, onMounted } from "vue";
    import axios, { AxiosError } from "axios";
    import { jwtDecode } from "jwt-decode";
    import { useRoute, useRouter } from "vue-router";
    import authModule from "@/assets/utils/auth";

    // API endpoints
    const API_BASE = "http://127.0.0.1:8000";
    const LOGIN_URL = `${API_BASE}/token`;
    const CAPTCHA_URL = `${API_BASE}/captcha`;

    const { setToken } = authModule;

    interface FormData {
        username: string;
        password: string;
        remember: boolean;
        capchaId: string;
        capchaText: string;
    }

    interface DecodedToken {
        sub: string;
        [key: string]: unknown;
    }

    const imageSrc = ref<string>("");
    const form_data = reactive<FormData>({
        username: "",
        password: "",
        remember: false,
        capchaId: "",
        capchaText: "",
    });

    const isLoading = ref(false);
    const error = ref(false);
    const error_msg = ref("");
    const route = useRoute();
    const router = useRouter();
    const emits = defineEmits<{ login: [userid: string] }>();

    const setErrorMessage = (message: string): void => {
        error_msg.value = message;
        error.value = true;
    };

    const clearError = (): void => {
        error_msg.value = "";
        error.value = false;
    };

    const fetchCaptcha = async (): Promise<void> => {
        try {
            const response = await axios.get(`${CAPTCHA_URL}?t=${Date.now()}`, {
                responseType: "blob",
            });

            form_data.capchaId = response.headers["x-captcha-id"] as string;
            imageSrc.value = URL.createObjectURL(response.data);
        } catch (err) {
            const error = err as AxiosError;
            console.error("Failed to fetch captcha:", error);
            setErrorMessage("Network error, unable to connect to server.");
        }
    };

    const refreshCaptcha = async (): Promise<void> => {
        await fetchCaptcha();
        form_data.capchaText = "";
    };

    onMounted(() => {
        fetchCaptcha();
    });

    const isFormValid = (): boolean => {
        const isUsernameValid = 
            form_data.username && 
            form_data.username.length <= MAX_LENGTH && 
            EMAIL_REGEX.test(form_data.username);
            
        const isPasswordValid = 
            form_data.password && 
            form_data.password.length <= MAX_LENGTH;
            
        const isCaptchaValid = 
            form_data.capchaText && 
            form_data.capchaText.length <= MAX_LENGTH;

        return !!(isUsernameValid && isPasswordValid && isCaptchaValid);
    };

    const submit = async (): Promise<void> => {
        if (!isFormValid()) {
            return;
        }

        isLoading.value = true;
        clearError();

        const formData = new FormData();
        formData.append("username", form_data.username);
        formData.append("password", form_data.password);
        formData.append("remember", String(form_data.remember));
        formData.append("captcha_id", form_data.capchaId);
        formData.append("captcha_input", form_data.capchaText);

        try {
            const response = await axios.post(LOGIN_URL, formData);
            const token = response.data.access_token;

            const decodedToken = jwtDecode<DecodedToken>(token);
            console.log("Token parsed:", decodedToken);

            setToken(token);
            emits("login", decodedToken.sub);

            const redirectPath = (route.query.redirect as string) || "/";
            await router.push(redirectPath);
        } catch (err) {
            const error = err as AxiosError;
            console.error("Login failed:", error);
            setErrorMessage("Login failed, please check your credentials.");
        } finally {
            isLoading.value = false;
        }
    };

    // Validation rules
    const EMAIL_REGEX = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    const MAX_LENGTH = 20;

    const rules = {
        required: (value: string): boolean | string => !!value || "Cannot be empty.",
        max: (value: string): boolean | string => (value?.length ?? 0) <= MAX_LENGTH || `Max ${MAX_LENGTH} characters allowed.`,
        username: (value: string): boolean | string =>
            EMAIL_REGEX.test(value) || "Please enter a valid email address",
    };

</script>
<template>
  <v-container :height="containerHeight" class="container">
    <div class="div_messages" ref="div_messages_ref">
      <div class="messages">
        <div
          v-for="(message, index) in chatHistory"
          :key="index"
          class="message"
          :class="message.role"
        >
          <div class="ma-2 pa-2" :class="message.role">
            <v-icon
              start
              icon="mdi-account"
              v-if="message.role === 'user'"
              color="blue"
            ></v-icon>
            <v-icon
              start
              icon="mdi-headset"
              v-if="message.role === 'agent'"
              color="green"
            ></v-icon>
            {{ message.text }}
            <span style="color: gray; margin-left: 5px">{{
              message.time
            }}</span>
          </div>
        </div>
      </div>
      <div v-if="isWaitingForReply" class="waiting">Please wait...</div>
    </div>

    <v-container class="div_input">
      <v-text-field
        v-model="newMessage"
        label="Please enter your question."
        type="text"
        variant="outlined"
        clearable
        append-inner-icon="mdi-send"
        @click:append-inner="sendMessage"
        @keyup.enter="sendMessage"
        :disabled="isWaitingForReply"
      >
        <template v-slot:prepend>
          <v-tooltip location="bottom">
            <template v-slot:activator="{ props }">
              <v-icon v-bind="props" icon="mdi-help-circle-outline"></v-icon>
            </template>

            {{ tootTip }}
          </v-tooltip>
        </template>

        <template v-slot:append-inner>
          <v-fade-transition leave-absolute>
            <v-progress-circular
              v-if="isWaitingForReply"
              color="info"
              size="24"
              indeterminate
            ></v-progress-circular>
          </v-fade-transition>
        </template>

        <template v-slot:append>
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" class="mt-n2">
                <v-icon icon="mdi-menu"></v-icon>
              </v-btn>
            </template>

            <v-card>
              <v-card-text class="pa-6">
                <v-btn color="primary" variant="text" @click="clearChatHistory">
                  <v-icon icon="mdi-delete" start></v-icon>

                  Clear chat history 
                </v-btn>
              </v-card-text>
            </v-card>
          </v-menu>
        </template>
      </v-text-field>
    </v-container>
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, computed, watch } from "vue";

interface ServiceInfo {
  name: string;
  url: string;
}

interface ChatMessage {
  role: "user" | "agent";
  text: string;
  rawTime: string;
  time: string;
}

interface ApiResponse {
  desc: string;
}

interface AxiosError {
  message: string;
  response?: {
    status: number;
  };
}

const serviceInfo = {
  name: "consult",
  url: "http://127.0.0.1:8000/consulting/chat",
};

const tootTip: Ref<string> = ref("More information, please contact email: dengguning@gmail.com");
const isWaitingForReply: Ref<boolean> = ref(false);
const newMessage: Ref<string> = ref("");

// handle chat history
const chatHistory: ChatMessage[] = reactive([]);

const saveChatHistory = (): void => {
  localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
};

const clearChatHistory = () => {
  chatHistory.splice(0, chatHistory.length);
  saveChatHistory();
};

const loadChatHistory = (): void => {
  const savedHistory = localStorage.getItem("chatHistory");
  if (savedHistory) {
    for (const item of JSON.parse(savedHistory) as ChatMessage[]) {
      item.time = getFriendlyTime(item.rawTime);
      chatHistory.push(item);
    }
  }
};

// handle send message
import axiosInstance from "@/assets/utils/axiosInstance";

const sendMessage = () => {
  newMessage.value = newMessage.value.trim();
  if (!newMessage.value.trim()) return;
  let rawTime = getCurrentTime();
  chatHistory.push({
    role: "user",
    text: newMessage.value.trim(),
    rawTime: rawTime,
    time: getFriendlyTime(rawTime),
  });
  let q = newMessage.value;
  newMessage.value = "";
  saveChatHistory();

  isWaitingForReply.value = true;

  axiosInstance
    .post(serviceInfo.url, {
      question: q,
      stream: false,
    })
    .then(
      (response) => {
        let resTime = getCurrentTime();
        let answer = response.data.answer;
        chatHistory.push({
          role: "agent",
          text: answer,
          rawTime: resTime,
          time: getFriendlyTime(resTime),
        });
        isWaitingForReply.value = false;
        saveChatHistory();
      },
      (error: AxiosError) => {
        console.log(error);
        newMessage.value = error.message;
        isWaitingForReply.value = false;
        if (error.response && error.response.status === 401) {
          // emits("navigate", "/" + serviceInfo.name);
          
        }
      }
    );
};

// handle time format
const getCurrentTime = (): string => {
  const now = new Date();
  return formatTime(now);
};

// convert time to yyyy-mm-dd hh:mm
const formatTime = (time: Date): string => {
  const year = time.getFullYear();
  const month = (time.getMonth() + 1).toString().padStart(2, "0"); // month is 0-based
  const day = time.getDate().toString().padStart(2, "0");
  const hours = time.getHours().toString().padStart(2, "0");
  const minutes = time.getMinutes().toString().padStart(2, "0");

  const formattedDate = `${year}-${month}-${day} ${hours}:${minutes}`;
  return formattedDate;
};

// convert time to friendly format
const getFriendlyTime = (dateStr: string): string => {
  // parse date string
  const inputDate = new Date(dateStr);

  // get current time and reset time to 00:00:00
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()); 

  // get yesterday time and reset time to 00:00:00
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1); // set time to 00:00:00

  // 格式化小时和分钟
  const hours = inputDate.getHours().toString().padStart(2, "0");
  const minutes = inputDate.getMinutes().toString().padStart(2, "0");

  // compare date and return formatted string
  if (inputDate >= today) {
    // if time is today, return time in format hh:mm
    return `${hours}:${minutes}`;
  } else if (inputDate >= yesterday) {
    // if time is yesterday, return time in format "yesterday hh:mm"
    return `Yesterday ${hours}:${minutes}`;
  } else {
    // 如果是其它时间 if time is other time, return time in format "yyyy-mm-dd hh:mm"
    const year = inputDate.getFullYear();
    const month = (inputDate.getMonth() + 1).toString().padStart(2, "0");
    const day = inputDate.getDate().toString().padStart(2, "0");
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  }
};

const div_messages_ref: Ref<HTMLElement | null> = ref(null);

// listen change of chat
watch(chatHistory, async () => {
  // wait for the DOM to update and scroll to the bottom.
  await nextTick();
  if (div_messages_ref.value) {
    //console.log("div_messages_ref:", div_messages_ref.value);
    div_messages_ref.value.scrollTop = div_messages_ref.value.scrollHeight;
  }
});

// scroll to the bottom of div
const scrollToBottom = (): void => {
  if (div_messages_ref.value) {
    //console.log(div_messages_ref.value);
    div_messages_ref.value.scrollTop = div_messages_ref.value.scrollHeight;
  }
};

onMounted(() => {
  loadChatHistory();
  scrollToBottom();
});

const containerHeight = computed((): string => {
  return "calc(100vh - 64px)"; // the toolbar's default height is 64px, which is just enough to fill the entire screen.
});
</script>


<style>
.container {
  display: flex;
  flex-direction: column;
}
.div_messages {
  flex: 1; /* div_messages fills the remaining space */
  overflow-y: auto; /* show vertical scrollbar when height exceeds */
  padding-bottom: 16px;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.div_input {
  display: flex;
  align-items: stretch; /* 确保子元素（input）与div_input高度相同 */
  margin: 0; /* 移除默认边距 */
  padding: 0; /* 移除默认内边距 */
}

.message {
  display: flex;
  align-items: center;
  max-width: 80%;
  padding: 8px;
  border-radius: 8px;
}
.message.user {
  align-self: flex-end;
}
.message.agent {
  align-self: flex-start;
}

.waiting {
  text-align: center;
  margin-top: 10px;
  font-style: italic;
}
</style>
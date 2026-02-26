<template>
  <v-app>
    <v-navigation-drawer
      v-model="drawer"
      :rail="rail"
      permanent
      @click="rail = false"
    >
      <v-list-item
        prepend-avatar="@/assets/image/myavatar.jpg"
        title="LLM Client"
        nav
      >
        <template v-slot:append>
          <v-btn
            icon="mdi-chevron-left"
            variant="text"
            @click.stop="rail = !rail"
          ></v-btn>
        </template>
      </v-list-item>

      <v-divider></v-divider>

      <v-list density="compact" nav>
        <v-list-item
          v-for="(item, i) in menuItems"
          :key="i"
          :prepend-icon="item.icon"
          :title="item.title"
          :value="item.value"
          @click="navigate(item.route)"
        ></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar density="compact" style="padding-right: 1%">
      <v-container
        style="width: 200px; text-align: bottom; padding-bottom: 0px"
      >
        <v-app-bar-title>
          <v-btn icon="mdi-home-variant" to="/"></v-btn>
        </v-app-bar-title>
      </v-container>

     <v-spacer></v-spacer>
      <v-btn icon @click="changeTheme" style="margin-right: 4%">
        <v-icon
          :icon="myTheme ? 'mdi-weather-night' : 'mdi-weather-sunny'"
        ></v-icon>
      </v-btn>

      <v-btn class="primary" variant="outlined" to="/login" v-if="!isLoggedIn">
        Log in
      </v-btn>
      <div v-else>
        <v-chip prepend-icon="mdi-account-outline">{{userName}}</v-chip>
        <v-btn icon="mdi-exit-to-app" @click="onLogout" ></v-btn>
      </div>      
    </v-app-bar>

    <v-main style="margin: 16px">
      <router-view  @login="onLogin" @navigate="navigate" v-slot="{ Component }">
        <v-slide-x-reverse-transition>
          <component :is="Component" />
        </v-slide-x-reverse-transition>
      </router-view>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
  import { ref, computed, type Ref } from "vue";
  import { useRouter } from "vue-router";
  import { useTheme } from "vuetify";
  import authModule from "@/assets/utils/auth";

  // Navigation drawer state
  const drawer: Ref<boolean> = ref(true);
  const rail: Ref<boolean> = ref(true);

  // Authentication state
  const isLoggedIn: Ref<boolean> = ref(false);
  const userName: Ref<string> = ref("Not logged in");

  // Initialize authentication
  const userId = authModule.getUserId();
  if (userId) {
    userName.value = userId;
    isLoggedIn.value = true;
  }

  // Theme management
  const theme = useTheme();
  const myTheme = computed({
    get: () => theme.global.name.value === "dark",
    set: (isDark: boolean) => {
      theme.global.name.value = isDark ? "dark" : "light";
    },
  });

  // Menu items
  const menuItems = ref([
    {
      icon: "mdi-comment-question-outline",
      title: "Consult",
      value: "consult",
      route: "/consult",
    },
    {
      icon: "mdi-translate",
      title: "Translate",
      value: "translate",
      route: "/translate",
    },
  ]);

  // Router and navigation
  const router = useRouter();
  const { checkLoggedIn, logout } = authModule;

  // Event handlers
  const onLogin = (name: string): void => {
    userName.value = name;
    isLoggedIn.value = true;
  };

  const onLogout = (): void => {
    logout();
    isLoggedIn.value = false;
  };

  const changeTheme = (): void => {
    myTheme.value = !myTheme.value;
  };

  const navigate = (route: string): void => {
    if (route === "/" || checkLoggedIn()) {
      router.push(route);
    } else {
      router.push({ path: "/login", query: { redirect: route } });
    }
  };
  
</script>

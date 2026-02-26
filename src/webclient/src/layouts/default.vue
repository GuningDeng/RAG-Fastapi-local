<template>
  <v-main>
    <div>
      <router-view @login="onLogin" @navigate="onNavigate" />
    </div>
  </v-main>

  <AppFooter />
</template>

<script lang="ts" setup>
  const onLogin = (userId: string) => {
    console.log("User logged in:", userId);
  };

  const onNavigate = (path: string) => {
    console.log("Navigating to:", path);
  };

  defineEmits<{
    login: [userId: string];
    navigate: [path: string];
  }>();
</script>

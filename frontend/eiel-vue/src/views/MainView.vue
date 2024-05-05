<script setup>

import { useRouter } from 'vue-router';
const router = useRouter();

import { useUserStore } from '@/stores/userStore';
const userStore = useUserStore();

userStore.loadToken();

if (!userStore.user.token) {
    router.replace('/login');    
} else {
    router.replace('/map');
}

</script>

<template>
    <div>
    </div>
</template>
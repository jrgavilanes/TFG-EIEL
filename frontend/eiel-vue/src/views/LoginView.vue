<script setup>
import Swal from 'sweetalert2';

import { ref } from 'vue';

import { useUserStore } from '@/stores/userStore';
const userStore = useUserStore();

const username = ref('');
const password = ref('');

const login = async () => {

    const response = await fetch(`api/auth/validate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: username.value,
            password: password.value,
        }),
    });

    if (!response.ok) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Usuario o contraseña incorrectos',
        });
        return;
    }

    const jwt = await response.json();
    userStore.login(jwt);

};
</script>

<template>
    <section class="bg-gray-50 h-screen">
        <div class="flex flex-col items-center justify-start px-6 pb-8 mx-auto md:h-screen lg:py-0">
            <!-- <a href="#" class="flex items-center text-2xl font-semibold text-gray-900 dark:text-white">
                <img class="w-32 h-32" :src="logo" alt="logo">
            </a> -->
            <p class="text-xl font-bold mb-6 my-12">TFG EIEL 1</p>
            <div class="w-full bg-white rounded-lg shadow md:mt-0 sm:max-w-md xl:p-0 ">
                <div class="p-6 space-y-4 md:space-y-6 sm:p-8">
                    <h1 class="text-xl font-bold leading-tight tracking-tight text-gray-900 md:text-2xl ">
                        Login
                    </h1>
                    <form @submit.prevent="login" class="space-y-4 md:space-y-6">
                        <div>
                            <label for="username" class="block mb-2 text-sm font-medium text-gray-900 ">
                                Nombre de usuario
                            </label>
                            <input v-model="username" type="username" name="username" id="username"
                                class="bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 "
                                placeholder="Escribe tu nombre de usuario" required="">
                        </div>
                        <div>
                            <label for="password" class="block mb-2 text-sm font-medium text-gray-900 ">Password</label>
                            <input v-model="password" type="password" name="password" id="password"
                                placeholder="Escribe tu clave de usuario"
                                class="bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 "
                                required="">
                        </div>

                        <button type="submit"
                            class="w-full text-white bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
                            Entrar
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </section>
</template>
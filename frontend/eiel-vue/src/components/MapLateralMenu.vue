<script setup>
import Swal from 'sweetalert2';

import { useMapStore } from '../stores/mapStore.js'
const mapStore = useMapStore()

import { useUserStore } from '@/stores/userStore';
const userStore = useUserStore();
userStore.loadToken();


import iconClose from './icons/iconClose.vue'
import { LABELS } from '../composables/mapsComposable.js'

const logout = () => {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "¿Quieres cerrar la sesión?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            userStore.logout();
        }
    });
}


const goToStreet = async (streetName) => {
    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${streetName}`);
    const results = await response.json();
    if (results.length > 0) {
        const { lat, lon } = results[0];
        mapStore.addMarker(lon, lat);
        mapStore.map.flyTo({ center: [lon, lat], zoom: 17 });
    } else {
        Swal.fire({
            icon: 'error',
            title: 'No se encontró la calle',
            text: `No se encontró ninguna calle con el nombre "${streetName}".`,
        });
    }
}
</script>

<template>
    <div v-show="mapStore.showMenu" class="w-[300px] absolute top-0 left-0 bottom-0 z-50 bg-slate-100/90 select-none">
        <div class="absolute bottom-0 top-0 overflow-y-auto overflow-x-hidden">
            <div class="fixed w-[300px] z-50 p-2 bg-slate-300 flex justify-between items-center">
                <p>Menú de opciones</p>
                <a href="/">
                    <span class="text-blue-700 font-bold text-xl">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                            stroke="currentColor" class="w-6 h-6">
                            <path stroke-linecap="round" stroke-linejoin="round"
                                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
                        </svg>
                    </span>
                </a>
                <div @click="mapStore.showMenu = !mapStore.showMenu" class="cursor-pointer">
                    <iconClose />
                </div>
            </div>
            <div class="p-1 mt-8">
                <form class="mt-2" @submit.prevent="goToStreet(mapStore.streetSearchInput)">
                    <div class="relative">
                        <div class="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
                            <svg class="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true"
                                xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
                                <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                                    stroke-width="2" d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z" />
                            </svg>
                        </div>
                        <input v-model="mapStore.streetSearchInput" type="search" id="default-search"
                            class="block w-full p-4 ps-10 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Calle, Código Postal" required>
                        <button type="submit"
                            class="text-white absolute end-2.5 bottom-2.5 bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-2 py-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">Buscar</button>
                    </div>
                </form>

                <p class="m-3 px-2 bg-slate-200 font-bold">Capas EIEL</p>
                <div v-for="capa in Object.keys(mapStore.listaEIEL)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaEIEL[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>

                <p class="m-3 px-2 bg-slate-200 font-bold">Delimitaciones</p>
                <div v-for="capa in Object.keys(mapStore.listaDelimitaciones)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaDelimitaciones[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>

                <p class="m-3 px-2 bg-slate-200 font-bold">Callejero</p>
                <div v-for="capa in Object.keys(mapStore.listaCallejero)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaCallejero[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
                <p class="m-3 px-2 bg-slate-200 font-bold">Lonjas / Mercados / Ferias</p>
                <div v-for="capa in Object.keys(mapStore.listaLonjasMercadosFerias)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaLonjasMercadosFerias[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
                <p class="m-3 px-2 bg-slate-200 font-bold">Parques y jardines</p>
                <div v-for="capa in Object.keys(mapStore.listaParquesJardines)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaParquesJardines[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
                <p class="m-3 px-2 bg-slate-200 font-bold">Residuos</p>
                <div v-for="capa in Object.keys(mapStore.listaResiduos)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaResiduos[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
                <p class="m-3 px-2 bg-slate-200 font-bold">Centros asistenciales</p>
                <div v-for="capa in Object.keys(mapStore.listaCentrosAsistencia)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaCentrosAsistencia[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
                <p class="m-3 px-2 bg-slate-200 font-bold">Centros sanitarios</p>
                <div v-for="capa in Object.keys(mapStore.listaCentrosSanitarios)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaCentrosSanitarios[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
                <p class="m-3 px-2 bg-slate-200 font-bold">Centros de enseñanza</p>
                <div v-for="capa in Object.keys(mapStore.listaCentrosEnsenanza)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaCentrosEnsenanza[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
                <p class="m-3 px-2 bg-slate-200 font-bold">Centros culturales</p>
                <div v-for="capa in Object.keys(mapStore.listaCentrosCulturales)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaCentrosCulturales[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
                <p class="m-3 px-2 bg-slate-200 font-bold">Instalaciones deportivas</p>
                <div v-for="capa in Object.keys(mapStore.listaInstalacionesDeportivas)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaInstalacionesDeportivas[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
                <p class="m-3 px-2 bg-slate-200 font-bold">Bomberos / Protección civil</p>
                <div v-for="capa in Object.keys(mapStore.listaBomberos)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaBomberos[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
                <p class="m-3 px-2 bg-slate-200 font-bold">Equipamientos municipales</p>
                <div v-for="capa in Object.keys(mapStore.listaEquipamientoMunicipales)" class="my-2" :key="capa">
                    <label class="py-2 px-6">
                        <input type="checkbox" v-model="mapStore.listaEquipamientoMunicipales[capa]">
                        {{ LABELS[capa] }}
                    </label>
                </div>
            </div>
            <div class="px-4 mb-4">
                <button type="button" @click="logout()"
                    class="w-full text-white bg-orange-600 hover:bg-orange-700 focus:ring-4 focus:outline-none focus:ring-orange-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-orange-600 dark:hover:bg-orange-700 dark:focus:ring-orange-800">
                    Desconectarte como {{ userStore.user.username }}
                </button>
            </div>
        </div>
    </div>
</template>

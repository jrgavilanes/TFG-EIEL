<script setup>
import { onMounted } from 'vue'
import Swal from 'sweetalert2';
import { Map, NavigationControl } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

import iconMenu from './icons/iconMenu.vue'
import MapLateralMenu from './MapLateralMenu.vue'

import { useMapStore } from '../stores/mapStore.js'
// import EquipmentCreate from './EquipmentCreate.vue';
import CementerioForm from './polls/CementerioForm.vue'
import CasaConsitorialForm from './polls/CasaConsitorialForm.vue'
import AssistanceCenterForm from './polls/AssistanceCenterForm.vue'
import ParkForm from './polls/ParkForm.vue';
import EducationalCenterForm from './polls/EducationalCenterForm.vue';
import MedicalCenterForm from './polls/MedicalCenterForm.vue';
import CulturalCenterForm from './polls/CulturalCenterForm.vue';
import UnusedBuildingForm from './polls/UnusedBuildingForm.vue';
import SportsFacilityForm from './polls/SportsFacilityForm.vue';
import MarketsForm from './polls/MarketsForm.vue';
import SlaughterhouseForm from './polls/SlaughterhouseForm.vue';
import MortuaryForm from './polls/MortuaryForm.vue';
import CivilProtectionForm from './polls/CivilProtectionForm.vue';
import LandfillForm from './polls/LandfillForm.vue';

import { useUserStore } from '@/stores/userStore';
const userStore = useUserStore();



const mapStore = useMapStore()

async function checkToken() {
        const data = await fetch(`/api/cemeteries/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + userStore.user.token,
            }
        })

        if (data.status === 401) {
            Swal.fire({
                title: 'Error!',
                text: 'Token de seguridad inválido. Por favor, inicie sesión nuevamente.',
                icon: 'error',
                confirmButtonText: 'OK',
                timer: 3000
            }).then(() => {
                // router.replace({ name: 'Login' });
                window.location.href = '/login';
                return;
            });
        }
        // console.log('Token válido')
    }

async function initCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const mediaDevices = await navigator.mediaDevices.enumerateDevices();
        const cameraDevices = mediaDevices.filter((device) => device.kind === "videoinput");
        // console.log('cameraDevices', cameraDevices);
        // console.log('stream', stream);
    } catch (error) {
        alert('No tiene permisos para acceder a la cámara:', error);
    }
}

async function initGPS() {    
    if (navigator.permissions && navigator.permissions.query) {
        navigator.permissions.query({ name: 'geolocation' }).then(function (result) {
            const permission = result.state;
            if (permission === 'granted' || permission === '   ' || permission === 'prompt') {
                // console.log('Geolocalización permitida');
            } else if (permission === 'denied') {
                alert("El permiso de geolocalización está denegado. Para activarlo acceda a la URL de la aplicación en el navegador y actívelo desde ahí");
            }
        });
    } else if (navigator.geolocation) {
        // console.log('Geolocalización permitida');
    }
}

const startPoll = async () => {
    Swal.fire({
        title: "¿Desea dar de alta nuevo equipamiento?",
        text: '',
        icon: 'question',
        input: 'select',
        inputOptions: {
            "CC": "Casa consistorial",
            "CE": "Cementerio",
            "AS": "Centro asistencial",
            "EN": "Centro de enseñanza",
            "SA": "Centro sanitario",
            "CU": "Centro cultural",
            "SU": "Edificio público sin uso",
            "ID": "Instalación deportiva",
            "LM": "Lonja o mercado o feria",
            "MT": "Matadero",
            "PJ": "Parque",
            "TA": "Tanatorio",
            "IP": "Protección civil",
            "VT": "Vertido encuestado",
        },
        inputPlaceholder: 'Tipo equipamiento',
        showCancelButton: true,
        cancelButtonText: 'Cancelar',
        confirmButtonText: 'Dar de alta',
        inputValidator: (value) => {
            if (!value) {
                return 'Debes seleccionar un tipo de equipamiento'
            }
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const opcionSeleccionada = result.value;
            // router.push({
            //     name: 'create-equipment', params: {
            //         tipo_equipamiento: opcionSeleccionada,
            //         mi_etiqueta: feature.properties.mi_etiqueta,
            //         lat: e.lngLat.lat,
            //         lng: e.lngLat.lng,
            //         geom: feature.properties.geom,
            //         field_nomecalles: `${feature.source}|${feature.properties.gid}`
            //     }
            // })
            Object.assign(mapStore.payload, {
                gid: null,
                tipo_equipamiento: opcionSeleccionada,
                mi_etiqueta: null,
                lat: mapStore.currentMarker.getLngLat().lat,
                lng: mapStore.currentMarker.getLngLat().lng,
                geom: null,
                field_nomecalles: null
            });
            mapStore.showEquipmentForm = true;
        }
    });
}

onMounted(() => {
    
    // initCamera();
    // initGPS();
    checkToken();

    mapStore.map = new Map({
        container: 'map',
        style: {
            version: 8,
            glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
            sources: {
                open_street_map: {
                    type: "raster",
                    tiles: [
                        "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                    ],
                    tileSize: 256,
                    attribution:
                        `TFG EIEL ${new Date().getFullYear()}. Server:${window.location.hostname}`
                },
                rasterLayer: {
                    type: "raster",
                    tiles: [
                        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    ],
                    tileSize: 256,
                    attribution:
                        `TFG EIEL ${new Date().getFullYear()}. Server:${window.location.hostname}`
                },
                muni2022: {
                    type: "vector",
                    tiles: [`${mapStore.TEGOLA_DOMAIN}/maps/eiel/muni2022/{z}/{x}/{y}.vector.pbf?`],
                },
                dist2022: {
                    type: "vector",
                    tiles: [`${mapStore.TEGOLA_DOMAIN}/maps/eiel/dist2022/{z}/{x}/{y}.vector.pbf?`],
                },
                nucleos: {
                    type: "vector",
                    tiles: [`${mapStore.TEGOLA_DOMAIN}/maps/eiel/nucleos/{z}/{x}/{y}.vector.pbf?`],
                    tolerance: 0,
                },
            },
            layers: [
                {
                    id: "open_street_map",
                    type: "raster",
                    source: "open_street_map",
                    paint: {},
                    'layout': {
                        'visibility': mapStore.listaDelimitaciones.open_street_map ? 'visible' : 'none'
                    }
                },
                {
                    id: "orthophoto",
                    type: "raster",
                    source: "rasterLayer",
                    paint: {
                        'raster-opacity': 0.7,
                    },
                    'layout': {
                        'visibility': mapStore.listaDelimitaciones.orthophoto ? 'visible' : 'none'
                    }
                },
                {
                    id: "dist2022",
                    source: "dist2022",
                    "source-layer": "dist2022",
                    type: "line",
                    paint: {
                        "line-color": "#FFFF00",
                        "line-width": 1,
                    },
                    'layout': {
                        'visibility': mapStore.listaDelimitaciones.dist2022 ? 'visible' : 'none'
                    }
                },
                {
                    id: "muni2022",
                    source: "muni2022",
                    minzoom: 5,
                    maxzoom: 13,
                    "source-layer": "muni2022",
                    type: "fill",
                    paint: {
                        'fill-color': [
                            'match',
                            ['get', 'eiel'],
                            1, '#0000ff', // Si el campo 'tipo' es 'carretera', el color será azul
                            0, '#eeeeee',
                            '#0000ff'         // Si el campo 'tipo' no coincide con ninguno, el color será gris
                        ],
                        "fill-opacity": 0.4,
                        "fill-outline-color": "#ffffff",
                    },
                    layout: {
                        visibility: mapStore.listaDelimitaciones.muni2022 ? 'visible' : 'none'
                    }
                },
                {
                    'id': 'muni2022_text',
                    minzoom: 5,
                    maxzoom: 13,
                    'type': 'symbol',
                    'source': 'muni2022',
                    "source-layer": "muni2022",
                    'layout': {
                        'text-field': ['get', 'etiqueta'], // Campo que contiene el texto a mostrar
                        'text-size': 12,
                        'text-offset': [0, 0.6], // Ajuste para la posición del texto
                        'text-anchor': 'top', // Anclaje del texto
                        'visibility': 'visible'
                    },
                    'paint': {
                        'text-color': '#000000',
                        "text-halo-color": "rgba(255,255,255,0.7)",
                        "text-halo-width": 2
                    }
                },
                {
                    id: "nucleos",
                    source: "nucleos",
                    "source-layer": "nucleos",
                    type: "line",
                    paint: {
                        "line-color": "#000000",
                        "line-width": 1,
                    },
                    'layout': {
                        'visibility': mapStore.listaDelimitaciones.nucleos ? 'visible' : 'none'
                    }
                }
            ]
        },
        center: [-3.6789, 40.5362],
        zoom: 8,
        maxZoom: 19
    });

    mapStore.map.on('click', (e) => {
        // if (!mapStore.showMenu) {
        //     mapStore.addMarker(e.lngLat.lng, e.lngLat.lat)
        // }
        // mapStore.showMenu = false
        mapStore.addMarker(e.lngLat.lng, e.lngLat.lat)
    })

    mapStore.loadRegularLayers()

    mapStore.map.addControl(
        new NavigationControl({
            visualizePitch: true
        })
    )

})
</script>

<template>
    <div v-show="!mapStore.showEquipmentForm">
        <div v-show="!mapStore.showMenu"
            class="absolute top-2 left-2 z-50 text-4xl bg-slate-200 rounded-md font-bold cursor-pointer"
            @click="mapStore.showMenu = !mapStore.showMenu">
            <iconMenu />
        </div>

        <button v-show="!userStore.user.is_desktop"
            class="absolute bottom-12 right-2 px-4 py-4 rounded-full bg-blue-700 active:bg-blue-400 text-white z-40 shadow-xl shadow-white"
            @click="mapStore.addMyLocation"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                stroke-width="2" stroke="currentColor" class="w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                <path stroke-linecap="round" stroke-linejoin="round"
                    d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
            </svg>
        </button>

        <button v-show="mapStore.currentMarker && userStore.user.role != 'cityhall'"
            class="absolute bottom-32 right-2 px-4 py-4 rounded-full bg-green-700 active:bg-green-400 text-white z-40 shadow-xl shadow-white"
            @click="startPoll"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="3"
                stroke="currentColor" class="w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
        </button>

        <MapLateralMenu />

        <div class="absolute top-0 bottom-0 left-0 right-0" id="map"></div>
    </div>
    <div v-show="mapStore.showEquipmentForm">
        <div class="px-4 pb-8">

            <CementerioForm v-if="mapStore.payload.tipo_equipamiento === 'CE'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <CasaConsitorialForm v-if="mapStore.payload.tipo_equipamiento === 'CC'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <AssistanceCenterForm v-if="mapStore.payload.tipo_equipamiento === 'AS'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <ParkForm v-if="mapStore.payload.tipo_equipamiento === 'PJ'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <EducationalCenterForm v-if="mapStore.payload.tipo_equipamiento === 'EN'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <MedicalCenterForm v-if="mapStore.payload.tipo_equipamiento === 'SA'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <CulturalCenterForm v-if="mapStore.payload.tipo_equipamiento === 'CU'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <UnusedBuildingForm v-if="mapStore.payload.tipo_equipamiento === 'SU'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <SportsFacilityForm v-if="mapStore.payload.tipo_equipamiento === 'ID'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <MarketsForm v-if="mapStore.payload.tipo_equipamiento === 'LM'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <SlaughterhouseForm v-if="mapStore.payload.tipo_equipamiento === 'MT'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <MortuaryForm v-if="mapStore.payload.tipo_equipamiento === 'TA'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <CivilProtectionForm v-if="mapStore.payload.tipo_equipamiento === 'IP'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

            <LandfillForm v-if="mapStore.payload.tipo_equipamiento === 'VT'" :lat="Number(mapStore.payload.lat)"
                :lng="Number(mapStore.payload.lng)" :mi_etiqueta="mapStore.payload.mi_etiqueta"
                :tipo_equipamiento="mapStore.payload.tipo_equipamiento" :geom="mapStore.payload.geom"
                :field_nomecalles="mapStore.payload.field_nomecalles" :gid="mapStore.payload.gid" />

        </div>
    </div>
</template>

<style scoped></style>

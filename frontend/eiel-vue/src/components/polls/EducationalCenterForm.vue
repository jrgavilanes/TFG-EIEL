<script setup>

const props = defineProps({
    lat: Number,
    lng: Number,
    geom: String,
    mi_etiqueta: String,
    tipo_equipamiento: String,
    field_nomecalles: String,
    gid: String
})

import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { aa_estado, aa_acceso_s_ruedas, aa_fase } from '@/composables/dominioComposable.js';
import { centro_ensenanza_ambito, centro_ensenanza_titular, nivel_ensenanza_nivel } from '@/composables/educationalCenterComposable.js';
import Swal from 'sweetalert2';

import { useMapStore } from '@/stores/mapStore.js'
const mapStore = useMapStore()

import { useUserStore } from '@/stores/userStore';
const userStore = useUserStore();

const router = useRouter();

const isLoading = ref(false);

const formData = reactive({
    gid: '',
    fase: aa_fase,
    clave: props.tipo_equipamiento,
    prov: '',
    mun: '',
    ent: '',
    poblamiento: '',
    orden_cent: '0',
    nombre: props.mi_etiqueta,
    ambito: '',
    titular: '',
    s_cubi: null,
    s_aire: null,
    s_sola: null,
    acceso_s_ruedas: '',
    estado: '',
    cod: '',
    borrado: 'N',
    field_nomecalles: props.field_nomecalles ? props.field_nomecalles : '',
    lat: props.lat,
    lng: props.lng,
    images: [],
    niveles: {},
    niveles_unidades: {},
    niveles_plazas: {},
    niveles_alumnos: {},
});

const getInfoByEquipmentId = async (gid) => {
    isLoading.value = true;
    try {
        const data = await fetch(`/api/educational-centers/${gid}`, {
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
                router.replace({ name: 'Login' });
                return;
            });
        }

        if (!data.ok) {
            const message = `An error has occured: ${data.status}`
            throw new Error(message)
        }
        const result = await data.json()

        isLoading.value = false;


        formData.gid = result.gid
        formData.nombre = result.nombre
        formData.ambito = result.ambito
        formData.titular = result.titular
        formData.s_cubi = result.s_cubi === null ? null : `${result.s_cubi}`
        formData.s_aire = result.s_aire === null ? null : `${result.s_aire}`
        formData.s_sola = result.s_sola === null ? null : `${result.s_sola}`
        formData.acceso_s_ruedas = result.acceso_s_ruedas
        formData.estado = result.estado
        formData.cod = result.cod
        formData.images = result.images
        formData.niveles = result.niveles
        formData.niveles_unidades = result.niveles_unidades
        formData.niveles_plazas = result.niveles_plazas
        formData.niveles_alumnos = result.niveles_alumnos

    } catch (error) {
        console.error("getInfo", error)
        isLoading.value = false;
        return error
    }

}

const deleteEquipment = (gid) => {
    Swal.fire({
        title: '¿Borrar equipamiento junto con todas su fotos?',
        text: "No podrás revertir esto!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, bórralo!',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/educational-centers/${gid}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + userStore.user.token,
                }
            })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(error => {
                            throw new Error(error.detail);
                        });
                    }
                    Swal.fire({
                        title: 'Borrado!',
                        text: 'El equipamiento ha sido borrado.',
                        icon: 'success',
                        confirmButtonText: 'OK',
                        timer: 1500
                    }).then(() => {
                        // refresh layer map
                        fetch('/api/educational-centers/', {
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + userStore.user.token,
                            }
                        })
                            .then(response => response.json())
                            .then(data => {
                                mapStore.map.getSource('mi_centros_ensenanza').setData(data);
                                mapStore.map.setLayoutProperty("educapu", 'visibility', 'none')
                                mapStore.map.setLayoutProperty("educapu", 'visibility', 'visible')
                                mapStore.map.triggerRepaint();

                            })
                            .catch(error => console.error('Error:', error))
                            .finally(() => {
                                closeForm();
                            });

                    });

                })
                .catch((error) => {
                    Swal.fire({
                        title: 'Error!',
                        text: error?.message,
                        icon: 'error',
                        confirmButtonText: 'OK'
                    });
                    // console.error("Error:", error);
                });
        }
    })
}

const deleteImage = (idef) => {
    Swal.fire({
        title: '¿Borrar imagen?',
        text: "No podrás revertir esto!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, bórrala!',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            isLoading.value = true;
            const payload = {
                idef: idef
            }
            fetch(`/api/upload/${idef}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + userStore.user.token,
                },
                body: JSON.stringify(payload)
            })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(error => {
                            throw new Error(error.detail);
                        });
                    }
                    Swal.fire({
                        title: 'Borrado!',
                        text: 'La imagen ha sido borrada.',
                        icon: 'success',
                        confirmButtonText: 'OK',
                        timer: 1500
                    });
                    formData.images = formData.images.filter(image => image.idef !== idef);
                })
                .catch((error) => {
                    // console.error("Error:", error);
                    Swal.fire({
                        title: 'Error!',
                        text: error?.message,
                        icon: 'error',
                        confirmButtonText: 'OK'
                    });
                }).finally(() => {
                    isLoading.value = false;
                });
        }
    })

}

const updateImage = (idef, tipo, comentario) => {
    const payload = {
        idef: idef,
        tipo: tipo,
        comentario: comentario ? comentario : ''
    }

    fetch(`/api/upload/${idef}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + userStore.user.token,
        },
        body: JSON.stringify(payload)
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(error => {
                    throw new Error(error.detail);
                });
            }
            Swal.fire({
                title: 'Guardado!',
                text: 'La imagen se ha actualizado correctamente.',
                icon: 'success',
                confirmButtonText: 'OK',
                timer: 1500
            });
        })
        .catch((error) => {
            Swal.fire({
                title: 'Error!',
                text: error?.message,
                icon: 'error',
                confirmButtonText: 'OK'
            });
        });

}


const getInfoByCoords = async (lat, lng, geom) => {
    try {
        let url = `/api/helpers/info?lat=${lat}&lng=${lng}`;
        if (geom) {
            url = `/api/helpers/info_by_geom?geom=${geom}`;
        }
        const data = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + userStore.user.token,
            }
        })
        if (!data.ok) {
            const message = `An error has occured: ${data.status}`
            throw new Error(message)
        }
        const result = await data.json()
        formData.lat = result.lat
        formData.lng = result.lng
        formData.fase = result.fase
        formData.ent = result.entidad
        formData.entidad_colectiva = result.entidad_colectiva
        formData.mun = result.municipio
        formData.prov = result.provincia
        formData.poblamiento = result.poblamiento
        formData.cod = `${props.tipo_equipamiento}${result.provincia}${result.municipio}${result.entidad}${result.poblamiento}`
        // console.log('llega', result)
    } catch (error) {
        console.error("getInfo", error)
        return error
    }
}

const postInfo = () => {
    // console.log('postInfo', formData)
    if (!formData.nombre) {
        Swal.fire({
            title: 'Error!',
            text: 'El campo nombre es obligatorio',
            icon: 'error',
            confirmButtonText: 'OK'
        });
        return;
    }

    formData.nombre = formData.nombre.substring(0, 50);

    // Sanitiza los niveles a enviar
    let niveles_activos = 0;
    for (let key in formData.niveles) {
        if (formData.niveles[key] === false) {
            delete formData.niveles[key];
            delete formData.niveles_unidades[key];
            delete formData.niveles_plazas[key];
            delete formData.niveles_alumnos[key];
        } else {
            formData.niveles_unidades[key] = formData.niveles_unidades[key] || 0;
            formData.niveles_plazas[key] = formData.niveles_plazas[key] || 0;
            formData.niveles_alumnos[key] = formData.niveles_alumnos[key] || 0;
            niveles_activos++;
        }
    }

    if (niveles_activos === 0) {
        alert('Debe seleccionar al menos un nivel')
        return;
    }

    if (formData.gid) {
        // Actualizo
        // console.log('llego')

        const payload = {
            gid: formData.gid,
            nombre: formData.nombre,
            ambito: formData.ambito,
            titular: formData.titular,
            s_cubi: formData.s_cubi || null,
            s_aire: formData.s_aire || null,
            s_sola: formData.s_sola || null,
            acceso_s_ruedas: formData.acceso_s_ruedas,
            estado: formData.estado,
            cod: formData.cod,
            niveles: formData.niveles,
            niveles_unidades: formData.niveles_unidades,
            niveles_plazas: formData.niveles_plazas,
            niveles_alumnos: formData.niveles_alumnos
        }


        fetch(`/api/educational-centers/${formData.gid}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + userStore.user.token,
            },
            body: JSON.stringify(payload)
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(error => {
                        throw new Error(error.detail);
                    });
                }
                Swal.fire({
                    title: 'El equipamiento se ha actualizado correctamente!',
                    text: '¿ Desea salir ?',
                    icon: 'success',
                    confirmButtonText: 'OK',
                    showCancelButton: true,
                    cancelButtonText: 'No'
                }).then((res) => {
                    if (res.isConfirmed) {
                        closeForm();
                    }
                })
            }).catch((error) => {
                Swal.fire({
                    title: 'Error!',
                    text: error?.message,
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            });
        return;
    } else {
        // Inserto registro

        const payload = {
            fase: formData.fase,
            clave: props.tipo_equipamiento,
            prov: formData.prov,
            mun: formData.mun,
            ent: formData.ent,
            poblamiento: formData.poblamiento,
            orden_cent: formData.orden_cent,
            nombre: formData.nombre,
            ambito: formData.ambito  || '',
            titular: formData.titular || '',
            s_cubi: formData.s_cubi || null,
            s_aire: formData.s_aire || null,
            s_sola: formData.s_sola || null,
            acceso_s_ruedas: formData.acceso_s_ruedas || '',
            estado: formData.estado,
            cod: formData.cod,
            borrado: formData.borrado,
            field_nomecalles: formData.field_nomecalles || null,
            lat: formData.lat,
            lng: formData.lng,
            niveles: formData.niveles,
            niveles_unidades: formData.niveles_unidades,
            niveles_plazas: formData.niveles_plazas,
            niveles_alumnos: formData.niveles_alumnos
        }
        fetch('/api/educational-centers/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + userStore.user.token,
            },
            body: JSON.stringify(payload)
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(error => {
                        throw new Error(error.detail);
                    });
                }
                return response.json()
            })
            .then(data => {
                // console.log('Success:', data);
                Swal.fire({
                    title: 'Guardado!',
                    text: 'El equipamiento se ha creado correctamente. ¿ Quieres añadir fotos ?',
                    icon: 'success',
                    confirmButtonText: 'OK',
                    showCancelButton: true,
                    cancelButtonText: 'No'
                }).then((response) => {
                    
                    mapStore.listaCentrosEnsenanza.educapu = true;
                    mapStore.listaCentrosEnsenanza.educase = true;
                    mapStore.listaCentrosEnsenanza.colegiosmayores = true;
                    mapStore.listaCentrosEnsenanza.univers = true;

                    if (response.isConfirmed) {
                        if (mapStore.showEquipmentForm) {
                            formData.gid = data.inserted_id;
                            getInfoByEquipmentId(formData.gid);
                            fetch('/api/educational-centers/', {
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': 'Bearer ' + userStore.user.token,
                                }
                            })
                                .then(response => response.json())
                                .then(data => {
                                    mapStore.map.getSource('mi_centros_ensenanza').setData(data);
                                    try {
                                        mapStore.map.moveLayer('educapu', 'mi_centros_ensenanza')
                                    } catch (error) {
                                        console.log('error al mover capa', error)
                                    }
                                    window.scrollTo({
                                        top: document.body.scrollHeight,
                                    });
                                })
                                .catch(error => console.error('Error:', error))
                        } else {
                            router.replace({ name: 'update-equipment', params: { gid: data.inserted_id, tipo_equipamiento: props.tipo_equipamiento } });
                        }
                    } else {
                        if (mapStore.showEquipmentForm) {
                            fetch('/api/educational-centers/', {
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': 'Bearer ' + userStore.user.token,
                                }
                            })
                                .then(response => response.json())
                                .then(data => {
                                    mapStore.map.getSource('mi_centros_ensenanza').setData(data);
                                    try {
                                        mapStore.map.moveLayer('educapu', 'mi_centros_ensenanza')
                                    } catch (error) {
                                        console.log('error al mover capa', error)
                                    }

                                })
                                .catch(error => console.error('Error:', error))
                                .finally(() => {
                                    closeForm();
                                });
                        } else {
                            closeForm();
                        }
                    }
                })
            })
            .catch((error) => {
                Swal.fire({
                    title: 'Error!',
                    text: error?.message,
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            });
    }
}

const handleFileChange = (event) => {
    isLoading.value = true;    
    navigator.geolocation.getCurrentPosition((coord)=>{
        const { latitude, longitude } = coord.coords;
        const file = event.target.files[0];
        const payload = new FormData();
        payload.append("new_file", file);
        const url = `/api/upload/${props.tipo_equipamiento}/${formData.gid}/${formData.cod}/${latitude}/${longitude}`;
        fetch( url, {
                method: "POST",
                headers: {
                    'Authorization': 'Bearer ' + userStore.user.token,
                },
                body: payload,
        }).then((response) => {
            return response.json();
        }).then((data) => {
            formData.images.push({
                minify_path: URL.createObjectURL(file),
                idef: data.idef,
                tipo: 'PG',
                comentario: ''
            });
            Swal.fire({
                title: 'Guardado!',
                text: 'La imagen se ha subido correctamente.',
                icon: 'success',
                confirmButtonText: 'OK',
                timer: 1500
            }).then(() => {
                window.scrollTo(0, document.body.scrollHeight);
            });
        }).catch((error) => {
            console.error("Error:", error);
            alert('Error al subir la imagen', error);
        }).finally(() => {
            isLoading.value = false;
        });
    }, (error)=>{
        console.error("Error:", error);
        alert('Error al obtener la ubicación. Active la ubicación del dispositivo', error);
        isLoading.value = false;
    });    
}

onMounted(() => {
    // console.log('mounted');
    // console.log(props.lat, props.lng, props.mi_etiqueta, props.gid, props.geom);
    if (props.gid) {
        // console.log('update');
        getInfoByEquipmentId(props.gid);
    } else {
        getInfoByCoords(props.lat, props.lng, props.geom);
    }
});


const closeForm = () => {
    mapStore.currentMarker.remove()
    mapStore.currentMarker = null    

    if (mapStore.showEquipmentForm) {
        Object.assign(mapStore.payload, {
            tipo_equipamiento: '',
            mi_etiqueta: '',
            lat: '',
            lng: '',
            geom: '',
            field_nomecalles: ''
        });
        mapStore.showEquipmentForm = false;
    } else {
        window.location.replace('/');
    }
}

const isValidForm = () => {

    return formData.nombre &&
        formData.titular &&
        formData.acceso_s_ruedas &&
        formData.nombre && formData.nombre.length <= 50 &&
        formData.ambito &&
        formData.estado &&
        !isNaN(formData.s_cubi) && formData.s_cubi &&
        !isNaN(formData.s_aire) && formData.s_aire &&
        !isNaN(formData.s_sola) && formData.s_sola

}

</script>

<template>
    <div
        class="max-w-3xl mx-auto select-none overscroll-none flex justify-between items-center top-0 left-0 right-0 fixed z-40 bg-slate-50 shadow-md">
        <div class="flex justify-start">
            <button :disabled="isLoading" class="mx-2 hover:bg-slate-100 cursor-pointer pe-2 py-1" @click="closeForm()">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                    stroke="currentColor" class="w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
                </svg>
            </button>
            <p v-if="!formData.gid" class="font-bold text-xl md:text-2xl my-2">
                Alta equipamiento (Centro de enseñanza)
            </p>
            <p v-if="formData.gid" class="font-bold text-xl md:text-2xl my-2 text-ellipsis">
                Editar equipamiento (Centro de enseñanza)
            </p>
        </div>
        <p v-if="isLoading" class="text-sm text-gray-900 mx-2">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                stroke="currentColor" class="w-6 h-6 animate-spin">
                <path stroke-linecap="round" stroke-linejoin="round"
                    d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
        </p>
    </div>
    <div v-if="!isLoading">
        <form @submit.prevent="postInfo()" class="max-w-3xl mx-auto mt-28 select-none overscroll-none">

            <div class="grid md:grid-cols-1 md:gap-3">

                <div v-if="formData.gid" class="relative z-0 w-full mb-5 group">
                    <label for="acceso" class="block mb-2 text-sm font-medium text-gray-900 ">
                        Id: {{ formData.gid }}
                    </label>
                </div>

                <div class="relative z-0 w-full mb-5 group">
                    <input v-model="formData.nombre" type="text" name="nombre" id="nombre"
                        class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                        placeholder=" " required maxlength="50" />
                    <p v-if="!formData.nombre || formData.nombre.length > 50" class="text-red-500 text-xs mt-2">Campo
                        obligatorio de 50 caracteres máximo</p>

                    <label for="nombre"
                        class="peer-focus:font-medium absolute text-sm text-gray-500  duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600 peer-focus:dark:text-blue-500 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">
                        Nombre</label>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="ambito" class="block mb-2 text-sm font-medium text-gray-900 ">Ámbito</label>
                    <select v-model="formData.ambito" id="ambito"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in centro_ensenanza_ambito" :key="estado.valor" :value="estado.valor">{{
                estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.ambito" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="titular" class="block mb-2 text-sm font-medium text-gray-900 ">Titular</label>
                    <select v-model="formData.titular" id="titular"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in centro_ensenanza_titular" :key="estado.valor" :value="estado.valor">{{
                estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.titular" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>

                <div class="relative z-0 w-full mb-5 group">
                    <p class="text-xl">Niveles</p>
                    <hr class="mb-4 mt-2">
                    <div class="grid grid-cols-1 gap-2">
                        <div v-for="nivel in nivel_ensenanza_nivel" :key="nivel.valor">
                            <input v-model="formData.niveles[nivel.valor]" type="checkbox" :id="nivel.valor"
                                :value="nivel.valor" class="peer mx-4" />
                            <label :for="nivel.valor"
                                class="peer-focus:font-medium text-md text-gray-500  duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600  peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">
                                {{ nivel.descripcion }}
                            </label>
                            <div v-if="formData.niveles[nivel.valor]" class="mb-4 px-4">
                                <div>
                                    <p class="mx-4 py-2.5 text-xs text-zinc-700">
                                        Unidades de {{ nivel.descripcion }}
                                    </p>
                                    <input v-model="formData.niveles_unidades[nivel.valor]" type="tel"
                                        class="mx-4 block w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none  focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                                        placeholder="0" pattern="\d*" required />
                                    <p v-if="!formData.niveles_unidades[nivel.valor]"
                                        class="text-red-500 text-xs mx-4 mt-2">
                                        Campo numérico entero obligatorio
                                    </p>
                                </div>

                                <div>
                                    <p class="mx-4 py-2.5 text-xs text-zinc-700">
                                        Plazas de {{ nivel.descripcion }}
                                    </p>
                                    <input v-model="formData.niveles_plazas[nivel.valor]" type="tel"
                                        class="mx-4 block w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none  focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                                        placeholder="0" pattern="\d*" required />
                                    <p v-if="!formData.niveles_plazas[nivel.valor]"
                                        class="text-red-500 text-xs mx-4 mt-2">
                                        Campo numérico entero obligatorio
                                    </p>
                                </div>

                                <div>
                                    <p class="mx-4 py-2.5 text-xs text-zinc-700">
                                        Alumnos de {{ nivel.descripcion }}
                                    </p>
                                    <input v-model="formData.niveles_alumnos[nivel.valor]" type="tel"
                                        class="mx-4 block w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none  focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                                        placeholder="0" pattern="\d*" required />
                                    <p v-if="!formData.niveles_alumnos[nivel.valor]"
                                        class="text-red-500 text-xs mx-4 mt-2">
                                        Campo numérico entero obligatorio
                                    </p>
                                </div>

                            </div>


                        </div>
                    </div>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <input v-model="formData.s_cubi" type="tel" name="s_cubi" id="s_cubi"
                        class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none  focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                        placeholder="" required pattern="\d*" />
                    <p v-if="!formData.s_cubi || isNaN(Number(formData.s_cubi))" class="text-red-500 text-xs mt-2">
                        Campo numérico entero obligatorio
                    </p>
                    <label for="s_cubi"
                        class="peer-focus:font-medium absolute text-sm text-gray-500  duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600  peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">
                        Superfice cubierta (m2)
                    </label>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <input v-model="formData.s_aire" type="tel" name="s_aire" id="s_aire"
                        class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none  focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                        placeholder="" required pattern="\d*" />
                    <p v-if="!formData.s_aire || isNaN(Number(formData.s_aire))" class="text-red-500 text-xs mt-2">
                        Campo numérico entero obligatorio
                    </p>
                    <label for="s_aire"
                        class="peer-focus:font-medium absolute text-sm text-gray-500  duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600  peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">
                        Superficie aire libre (m2)
                    </label>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <input v-model="formData.s_sola" type="tel" name="s_sola" id="s_sola"
                        class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none  focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                        placeholder="" required pattern="\d*" />
                    <p v-if="!formData.s_sola || isNaN(Number(formData.s_sola))" class="text-red-500 text-xs mt-2">
                        Campo numérico entero obligatorio
                    </p>
                    <label for="s_sola"
                        class="peer-focus:font-medium absolute text-sm text-gray-500  duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600  peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">
                        Superfice solar (m2)
                    </label>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="estado" class="block mb-2 text-sm font-medium text-gray-900 ">Estado</label>
                    <select v-model="formData.estado" id="estado"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_estado" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.estado" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="acceso_s_ruedas" class="block mb-2 text-sm font-medium text-gray-900 ">
                        Acceso silla de ruedas
                    </label>
                    <select v-model="formData.acceso_s_ruedas" id="acceso_s_ruedas"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_acceso_s_ruedas" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.acceso_s_ruedas" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
            </div>
            <!-- botonera inferior -->
            <div v-if="!isLoading" class="flex justify-between items-center gap-2">
                <button v-if="formData.gid && userStore.user.role != 'cityhall'" type="button"
                    @click="deleteEquipment(formData.gid)"
                    class="self-stretch bg-red-50 hover:bg-red-100 focus:ring-4 focus:outline-none focus:ring-red-300 font-medium rounded-lg text-sm sm:w-auto px-5 py-2.5 text-center ">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                        stroke="currentColor" class="w-6 h-6">
                        <path stroke-linecap="round" stroke-linejoin="round"
                            d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                    </svg>
                </button>
                <button v-if="!isValidForm()" type="button" @click="postInfo()"
                    class="text-white bg-orange-700 focus:ring-4 focus:outline-none focus:ring-green-300 font-medium rounded-lg text-xs md:text-xl w-full px-5 py-2.5 text-center disabled:bg-gray-500">
                    Actualizar parcialmente
                </button>
                <button type="submit" :disabled="!isValidForm()"
                    class="self-stretch text-white bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-xs md:text-xl w-full px-5 py-2.5 text-center disabled:bg-gray-500">
                    Finalizar equipamiento
                </button>                
            </div>
            <!-- fin botonera inferior -->
        </form>


        <!-- listado de imagenes y boton subida foto -->
        <div v-show="formData.gid" class="max-w-2xl mx-auto select-none overscroll-none">
            <p v-if="formData.images.length" class="select-none text-xl font-bold mt-8">Imágenes asociadas</p>
            <div v-for="my_image in formData.images" :key="my_image.idef">
                <div class="bg-slate-50 p-4 mt-8">
                    <img v-if="my_image.minify_path" :src="my_image.minify_path" class="w-full my-4" alt="foto">
                    <div>
                        <div class="">
                            <select v-model="my_image.tipo"
                                class="w-full bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 ">
                                <option value="PG">Plano general</option>
                                <option value="PE">Perspectiva de estado</option>
                            </select>
                            <div class="my-4">
                                <textarea rows="4" v-model="my_image.comentario" maxlength="255"
                                    class="block p-2.5 w-full text-sm text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 "
                                    placeholder="Comentarios de imagen"></textarea>

                            </div>
                            <div v-if="userStore.user.role != 'cityhall'" class="flex gap-2">
                                <button type="button" :disabled="isLoading"
                                    class="text-white bg-red-700 hover:bg-red-800 focus:ring-4 focus:outline-none focus:ring-red-300 font-medium rounded-lg text-sm w-full sm:w-auto px-5 py-2.5 text-center dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-800"
                                    @click="deleteImage(my_image.idef)">
                                    <div class="flex flex-col items-center justify-between">
                                        <span>Borrar imagen</span>
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                            stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                                            <path stroke-linecap="round" stroke-linejoin="round"
                                                d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                                        </svg>
                                    </div>
                                </button>
                                <button type="button" :disabled="isLoading"
                                    class="disabled:bg-gray-600 text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm w-full sm:w-auto px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
                                    @click="updateImage(my_image.idef, my_image.tipo, my_image.comentario)">
                                    <div class="flex flex-col items-center justify-between">
                                        <span>Actualizar datos imagen</span>
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                                            stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                                            <path stroke-linecap="round" stroke-linejoin="round"
                                                d="M9 3.75H6.912a2.25 2.25 0 0 0-2.15 1.588L2.35 13.177a2.25 2.25 0 0 0-.1.661V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H15M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859M12 3v8.25m0 0-3-3m3 3 3-3" />
                                        </svg>
                                    </div>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- boton de subida de imagen -->
            <label v-if="!isLoading" class="block mb-2 text-sm font-medium text-gray-900 my-4" for="file_input">
                <div v-if="!userStore.user.is_desktop && userStore.user.role != 'cityhall'"
                    class="w-full focus:outline-none text-white bg-green-700 hover:bg-green-800 focus:ring-4 focus:ring-green-300 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2">
                   
                    <div class="flex flex-col items-center justify-between text-xl">
                        <span>Subir Nueva Imagen</span>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                            stroke="currentColor" class="w-12 h-12">
                            <path stroke-linecap="round" stroke-linejoin="round"
                                d="M6.827 6.175A2.31 2.31 0 0 1 5.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 0 0-1.134-.175 2.31 2.31 0 0 1-1.64-1.055l-.822-1.316a2.192 2.192 0 0 0-1.736-1.039 48.774 48.774 0 0 0-5.232 0 2.192 2.192 0 0 0-1.736 1.039l-.821 1.316Z" />
                            <path stroke-linecap="round" stroke-linejoin="round"
                                d="M16.5 12.75a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0ZM18.75 10.5h.008v.008h-.008V10.5Z" />
                        </svg>
                    </div>
                </div>
            </label>
            <input
                class="hidden w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
                id="file_input" type="file" @change="handleFileChange">
            <!-- fin boton de subida de imagen -->

        </div> 
        <!-- fin listado de imagenes y boton subida foto -->
    </div>
    <div v-if="isLoading" class="flex flex-col items-center justify-between mt-24">
        <div role="status"
            class="max-w-sm p-4 border border-gray-200 rounded shadow animate-pulse md:p-6 dark:border-gray-700">
            <div class="flex items-center justify-center h-48 mb-4 bg-gray-300 rounded dark:bg-gray-700">
                <svg class="w-10 h-10 text-gray-200 dark:text-gray-600" aria-hidden="true"
                    xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 20">
                    <path
                        d="M14.066 0H7v5a2 2 0 0 1-2 2H0v11a1.97 1.97 0 0 0 1.934 2h12.132A1.97 1.97 0 0 0 16 18V2a1.97 1.97 0 0 0-1.934-2ZM10.5 6a1.5 1.5 0 1 1 0 2.999A1.5 1.5 0 0 1 10.5 6Zm2.221 10.515a1 1 0 0 1-.858.485h-8a1 1 0 0 1-.9-1.43L5.6 10.039a.978.978 0 0 1 .936-.57 1 1 0 0 1 .9.632l1.181 2.981.541-1a.945.945 0 0 1 .883-.522 1 1 0 0 1 .879.529l1.832 3.438a1 1 0 0 1-.031.988Z" />
                    <path d="M5 5V.13a2.96 2.96 0 0 0-1.293.749L.879 3.707A2.98 2.98 0 0 0 .13 5H5Z" />
                </svg>
            </div>
            <div class="h-2.5 bg-gray-200 rounded-full dark:bg-gray-700 w-48 mb-4"></div>
            <div class="h-2 bg-gray-200 rounded-full dark:bg-gray-700 mb-2.5"></div>
            <div class="h-2 bg-gray-200 rounded-full dark:bg-gray-700 mb-2.5"></div>
            <div class="h-2 bg-gray-200 rounded-full dark:bg-gray-700"></div>
            <div class="flex items-center mt-4">
                <svg class="w-10 h-10 me-3 text-gray-200 dark:text-gray-700" aria-hidden="true"
                    xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                    <path
                        d="M10 0a10 10 0 1 0 10 10A10.011 10.011 0 0 0 10 0Zm0 5a3 3 0 1 1 0 6 3 3 0 0 1 0-6Zm0 13a8.949 8.949 0 0 1-4.951-1.488A3.987 3.987 0 0 1 9 13h2a3.987 3.987 0 0 1 3.951 3.512A8.949 8.949 0 0 1 10 18Z" />
                </svg>
                <div>
                    <div class="h-2.5 bg-gray-200 rounded-full dark:bg-gray-700 w-32 mb-2"></div>
                    <div class="w-48 h-2 bg-gray-200 rounded-full dark:bg-gray-700"></div>
                </div>
            </div>
            <span class="sr-only">Loading...</span>
        </div>
        <p class="text-slate-400 animate-ping mt-8">Actualizando datos...</p>
    </div>
</template>

<style></style>
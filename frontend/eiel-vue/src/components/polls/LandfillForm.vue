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
import { aa_estado, aa_fase, aa_sino, aa_sino_existe } from '@/composables/dominioComposable.js';
import { vert_encuestado_actividad, vert_encuestado_categoria, vert_encuestado_gestion, vert_encuestado_saturacion, vert_encuestado_tipo_ver, vert_encuestado_titular } from '@/composables/landfillComposable.js';
import Swal from 'sweetalert2';

import { useMapStore } from '@/stores/mapStore.js'
const mapStore = useMapStore()

import { useUserStore } from '@/stores/userStore';
const userStore = useUserStore();

const router = useRouter();

const isLoading = ref(false);

const nomecalles_layers = [
    "puntoslim",
    "peligrosos",
    "vertederos",
]

const refresh_nomecalles_layers = (layers) => {
    layers.forEach(layer => {
        mapStore.map.setLayoutProperty(layer, 'visibility', 'none')
        mapStore.map.setLayoutProperty(layer, 'visibility', 'visible')
    })
}

const enable_nomecalles_layers = (layers) => {
    layers.forEach(layer => {
        mapStore.listaResiduos[layer] = true
    })
}

const move_nomecalles_layers_behind_mine = (layers) => {
    layers.forEach(layer => {
        mapStore.map.moveLayer(layer, 'mi_vertederos')
    })
}

const removeMarkerFromMap = () => {
    mapStore.currentMarker.remove()
    mapStore.currentMarker = null
}


const formData = reactive({
    gid: '',
    fase: aa_fase,
    clave: props.tipo_equipamiento,
    prov: '',
    mun: '',
    ent: '',
    poblamiento: '',
    orden_ver: '0',
    internal_nombre: props.mi_etiqueta,
    is_greater_50k: '',
    tipo_ver: '',
    titular: '',
    gestion: '',
    olores: '',
    humos: '',
    cont_anima: '',
    r_inun: '',
    filtracion: '',
    impacto_v: '',
    frec_averia: '',
    saturacion: '',
    inestable: '',
    otros: '',
    capac_tot: null,
    capac_tot_porc: null,
    capac_ampl: '',
    capac_transf: null,
    vida_util: null,
    categoria: '',
    actividad: '',
    estado: '',
    cod: '',
    borrado: 'N',
    field_nomecalles: props.field_nomecalles ? props.field_nomecalles : '',
    lat: props.lat,
    lng: props.lng,
    images: [],
});

const getInfoByEquipmentId = async (gid) => {
    isLoading.value = true;
    try {
        const data = await fetch(`/api/landfills/${gid}`, {
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
        formData.internal_nombre = result.nombre
        formData.is_greater_50k = result.is_greater_50k == true ? 'SI' : 'NO'
        formData.tipo_ver = result.detail[0].tipo_ver 
        formData.titular = result.detail[0].titular
        formData.gestion = result.detail[0].gestion
        formData.olores = result.detail[0].olores
        formData.humos = result.detail[0].humos
        formData.cont_anima = result.detail[0].cont_anima
        formData.r_inun = result.detail[0].r_inun
        formData.filtracion = result.detail[0].filtracion
        formData.impacto_v = result.detail[0].impacto_v
        formData.frec_averia = result.detail[0].frec_averia
        formData.saturacion = result.detail[0].saturacion
        formData.inestable = result.detail[0].inestable
        formData.otros = result.detail[0].otros
        formData.capac_tot = result.detail[0].capac_tot === null ? null : `${result.detail[0].capac_tot}`
        formData.capac_tot_porc = result.detail[0].capac_tot_porc === null ? null : `${result.detail[0].capac_tot_porc}`
        formData.capac_ampl = result.detail[0].capac_ampl
        formData.capac_transf = result.detail[0].capac_transf === null ? null : `${result.detail[0].capac_transf}`
        formData.vida_util = result.detail[0].vida_util === null ? null : `${result.detail[0].vida_util}`
        formData.categoria = result.detail[0].categoria
        formData.actividad = result.detail[0].actividad
        formData.estado = result.detail[0].estado
        formData.cod = result.cod
        formData.images = result.images


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
            fetch(`/api/landfills/${gid}`, {
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
                        fetch('/api/landfills/', {
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + userStore.user.token,
                            }
                        })
                            .then(response => response.json())
                            .then(data => {
                                mapStore.map.getSource('mi_vertederos').setData(data);
                                refresh_nomecalles_layers(nomecalles_layers);
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
    if (!formData.internal_nombre || !formData.is_greater_50k || !formData.tipo_ver) {
        Swal.fire({
            title: 'Error!',
            text: 'Los campos nombre, tamaño de municipio y el tipo de vertido son obligatorios',
            icon: 'error',
            confirmButtonText: 'OK'
        });
        return;
    }

    if (!formData.tipo_ver || !formData.is_greater_50k) {
        Swal.fire({
            title: 'Error!',
            text: 'Los campos nombre y tamaño de municipio son obligatorios',
            icon: 'error',
            confirmButtonText: 'OK'
        });
        return;
    }
    formData.internal_nombre = formData.internal_nombre.substring(0, 40);


    if (formData.gid) {
        // Actualizo registro

        const payload = {
            gid: formData.gid,
            nombre: formData.internal_nombre,
            internal_nombre: formData.internal_nombre,
            is_greater_50k: formData.is_greater_50k == 'SI' ? true : false,
            tipo_ver: formData.tipo_ver || null,
            titular: formData.titular || null,
            gestion: formData.gestion || null,
            olores: formData.olores || null,
            humos: formData.humos || null,
            cont_anima: formData.cont_anima || null,
            r_inun: formData.r_inun || null,
            filtracion: formData.filtracion || null,
            impacto_v: formData.impacto_v || null,
            frec_averia: formData.frec_averia || null,
            saturacion: formData.saturacion || null,
            inestable: formData.inestable || null,
            otros: formData.otros || null,
            capac_tot: formData.capac_tot || null,
            capac_tot_porc: formData.capac_tot_porc || null,
            capac_ampl: formData.capac_ampl || null,
            capac_transf: formData.capac_transf || null,
            vida_util: formData.vida_util || null,
            categoria: formData.categoria || null,
            actividad: formData.actividad || null,
            estado: formData.estado || null,
        }


        fetch(`/api/landfills/${formData.gid}`, {
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
            orden_ver: formData.orden_ver,
            nombre: formData.internal_nombre,
            internal_nombre: formData.internal_nombre,
            is_greater_50k: formData.is_greater_50k == 'SI' ? true : false,
            tipo_ver: formData.tipo_ver || null,
            titular: formData.titular || null,
            gestion: formData.gestion || null,
            olores: formData.olores || null,
            humos: formData.humos || null,
            cont_anima: formData.cont_anima || null,
            r_inun: formData.r_inun || null,
            filtracion: formData.filtracion || null,
            impacto_v: formData.impacto_v || null,
            frec_averia: formData.frec_averia || null,
            saturacion: formData.saturacion || null,
            inestable: formData.inestable || null,
            otros: formData.otros || null,
            capac_tot: formData.capac_tot || null,
            capac_tot_porc: formData.capac_tot_porc || null,
            capac_ampl: formData.capac_ampl || null,
            capac_transf: formData.capac_transf || null,
            vida_util: formData.vida_util || null,
            categoria: formData.categoria || null,
            actividad: formData.actividad || null,
            estado: formData.estado || null,
            cod: formData.cod,
            borrado: 'N',
            field_nomecalles: formData.field_nomecalles || '',
            lat: formData.lat,
            lng: formData.lng,
        }

        fetch('/api/landfills/', {
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

                    enable_nomecalles_layers(nomecalles_layers);
                    
                    if (response.isConfirmed) {
                        if (mapStore.showEquipmentForm) {
                            formData.gid = data.inserted_id;
                            getInfoByEquipmentId(formData.gid);
                            fetch('/api/landfills/', {
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': 'Bearer ' + userStore.user.token,
                                }
                            })
                                .then(response => response.json())
                                .then(data => {
                                    mapStore.map.getSource('mi_vertederos').setData(data);
                                    try {
                                        move_nomecalles_layers_behind_mine(nomecalles_layers);
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
                            fetch('/api/landfills/', {
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': 'Bearer ' + userStore.user.token,
                                }
                            })
                                .then(response => response.json())
                                .then(data => {
                                    mapStore.map.getSource('mi_vertederos').setData(data);
                                    try {
                                        move_nomecalles_layers_behind_mine(nomecalles_layers);
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
    removeMarkerFromMap();
    
    // console.log(props.lat, props.lng, props.mi_etiqueta, props.gid, props.geom);
    if (props.gid) {
        // console.log('update');
        getInfoByEquipmentId(props.gid);
    } else {
        getInfoByCoords(props.lat, props.lng, props.geom);
    }
});


const closeForm = () => {
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

    return formData.internal_nombre && formData.internal_nombre.length <= 50 &&
        formData.is_greater_50k &&
        formData.tipo_ver &&
        formData.titular &&
        formData.gestion &&
        formData.olores &&
        formData.humos &&
        formData.cont_anima &&
        formData.r_inun &&
        formData.filtracion &&
        formData.impacto_v &&
        formData.frec_averia &&
        formData.saturacion &&
        formData.inestable &&
        formData.otros &&
        !isNaN(formData.vida_util) && formData.vida_util &&
        formData.categoria &&
        formData.actividad &&
        formData.estado

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
                Alta equipamiento (Vertido encuestado)
            </p>
            <p v-if="formData.gid" class="font-bold text-xl md:text-2xl my-2 text-ellipsis">
                Editar equipamiento (Vertido encuestado)
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
                    <input v-model="formData.internal_nombre" type="text" name="nombre" id="nombre"
                        class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                        placeholder=" " required maxlength="40" />
                    <p v-if="!formData.internal_nombre || formData.internal_nombre.length > 50"
                        class="text-red-500 text-xs mt-2">
                        Campo obligatorio y menor de 50 caracteres
                    </p>

                    <label for="nombre"
                        class="peer-focus:font-medium absolute text-sm text-gray-500  duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600 peer-focus:dark:text-blue-500 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">
                        Nombre
                    </label>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="greater_50k" class="block mb-2 text-sm font-medium text-gray-900 ">Municipio mayor de
                        50.000 habitantes</label>
                    <select v-model="formData.is_greater_50k" id="greater_50k"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected disabled value="">Elija una opción</option>
                        <option v-for="estado in aa_sino" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.is_greater_50k" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="tipo_ver" class="block mb-2 text-sm font-medium text-gray-900 ">Tipo</label>
                    <select v-model="formData.tipo_ver" id="tipo_ver"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in vert_encuestado_tipo_ver" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.tipo_ver" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="titular" class="block mb-2 text-sm font-medium text-gray-900 ">Titular</label>
                    <select v-model="formData.titular" id="titular"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in vert_encuestado_titular" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.titular" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="gestion" class="block mb-2 text-sm font-medium text-gray-900 ">Gestión</label>
                    <select v-model="formData.gestion" id="gestion"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in vert_encuestado_gestion" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.gestion" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="olores" class="block mb-2 text-sm font-medium text-gray-900 ">Olores</label>
                    <select v-model="formData.olores" id="olores"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_sino" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.olores" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="humos" class="block mb-2 text-sm font-medium text-gray-900 ">Humos</label>
                    <select v-model="formData.humos" id="humos"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_sino" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.humos" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="cont_anima" class="block mb-2 text-sm font-medium text-gray-900 ">Contaminación
                        animal</label>
                    <select v-model="formData.cont_anima" id="cont_anima"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_sino" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.cont_anima" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="r_inun" class="block mb-2 text-sm font-medium text-gray-900 ">Riesgo de
                        inundación</label>
                    <select v-model="formData.r_inun" id="r_inun"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_sino" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.r_inun" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="filtracion" class="block mb-2 text-sm font-medium text-gray-900 ">Filtración</label>
                    <select v-model="formData.filtracion" id="filtracion"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_sino" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.filtracion" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="impacto_v" class="block mb-2 text-sm font-medium text-gray-900 ">Impacto visual</label>
                    <select v-model="formData.impacto_v" id="impacto_v"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_sino" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.impacto_v" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="frec_averia" class="block mb-2 text-sm font-medium text-gray-900 ">Frecuencia de
                        averías</label>
                    <select v-model="formData.frec_averia" id="frec_averia"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_sino" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.frec_averia" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="saturacion" class="block mb-2 text-sm font-medium text-gray-900 ">Saturación</label>
                    <select v-model="formData.saturacion" id="saturacion"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in vert_encuestado_saturacion" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.saturacion" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="inestable" class="block mb-2 text-sm font-medium text-gray-900 ">Inestable</label>
                    <select v-model="formData.inestable" id="inestable"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_sino" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.inestable" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="otros" class="block mb-2 text-sm font-medium text-gray-900 ">Otros</label>
                    <select v-model="formData.otros" id="otros"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_sino" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.otros" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <input v-model="formData.capac_tot" type="tel" name="capac_tot" id="capac_tot"
                        class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none  focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                        placeholder="" pattern="\d*" />
                    <label for="capac_tot"
                        class="peer-focus:font-medium absolute text-sm text-gray-500  duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600  peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">
                        Capacidad total
                    </label>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <input v-model="formData.capac_tot_porc" type="tel" name="capac_tot_porc" id="capac_tot_porc"
                        class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none  focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                        placeholder="" pattern="\d*" />

                    <label for="capac_tot_porc"
                        class="peer-focus:font-medium absolute text-sm text-gray-500  duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600  peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">
                        Capacidad total porcentaje
                    </label>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="capac_ampl" class="block mb-2 text-sm font-medium text-gray-900 ">Capacidad de
                        ampliación</label>
                    <select v-model="formData.capac_ampl" id="capac_ampl"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in aa_sino_existe" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <input v-model="formData.capac_transf" type="text" name="capac_transf" id="capac_transf"
                        class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none  focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                        placeholder="" pattern="\d*" />
                    <label for="capac_transf"
                        class="peer-focus:font-medium absolute text-sm text-gray-500  duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600  peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">
                        Capacidad transferencia
                    </label>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <input v-model="formData.vida_util" type="tel" name="vida_util" id="vida_util"
                        class="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none  focus:outline-none focus:ring-0 focus:border-blue-600 peer"
                        placeholder="" required pattern="\d*" />
                    <p v-if="!formData.vida_util || isNaN(Number(formData.vida_util))"
                        class="text-red-500 text-xs mt-2">
                        Campo
                        numérico entero
                        obligatorio</p>
                    <label for="vida_util"
                        class="peer-focus:font-medium absolute text-sm text-gray-500  duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:start-0 rtl:peer-focus:translate-x-1/4 peer-focus:text-blue-600  peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">
                        Vida útil
                    </label>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="categoria" class="block mb-2 text-sm font-medium text-gray-900 ">Categoría</label>
                    <select v-model="formData.categoria" id="categoria"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in vert_encuestado_categoria" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.categoria" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
                </div>
                <div class="relative z-0 w-full mb-5 group">
                    <label for="actividad" class="block mb-2 text-sm font-medium text-gray-900 ">Actividad</label>
                    <select v-model="formData.actividad" id="actividad"
                        class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 ">
                        <option selected value="">Elija una opción</option>
                        <option v-for="estado in vert_encuestado_actividad" :key="estado.valor" :value="estado.valor">
                            {{ estado.descripcion }}
                        </option>
                    </select>
                    <p v-if="!formData.actividad" class="text-red-500 text-xs mt-2">Campo obligatorio</p>
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

        <!-- listado de imagenes -->
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
        <!-- fin listado de imagenes -->        
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
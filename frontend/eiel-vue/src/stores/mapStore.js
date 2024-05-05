import Swal from 'sweetalert2';
import { defineStore } from 'pinia'
import { ref, watch, reactive } from 'vue'
import { Marker } from 'maplibre-gl'

import { TEGOLA_DOMAIN } from '../config/urls.js'

import { useUserStore } from './userStore.js'



export const useMapStore = defineStore('mapStore', () => {

    const userStore = useUserStore()
    userStore.loadToken();

    const map = ref(null)
    const center = reactive({ lng: -3.6789, lat: 40.5362 })

    const payload = reactive({
        tipo_equipamiento: '',
        mi_etiqueta: '',
        lat: '',
        lng: '',
        geom: '',
        field_nomecalles: ''
    });

    const mi_etiqueta = ref("")
    const currentMarker = ref(null)
    const showMenu = ref(true)
    const showEquipmentForm = ref(false)
    const streetSearchInput = ref('')

    const tipo_equipamiento = ref('')

    const clearStreetSearchInput = () => {
        streetSearchInput.value = null
    }

    const listaEIEL = reactive({
        "mi_casas_consistoriales": false,
        "mi_cementerios": false,
        "mi_centros_asistencia": false,
        "mi_centros_ensenanza": false,
        "mi_centros_sanitarios": false,
        "mi_centros_culturales": false,
        "mi_edificios_sin_uso": false,
        "mi_instalaciones_deportivas": false,
        "mi_lonja_merca_feria": false,
        "mi_mataderos": false,
        "mi_parques": false,
        "mi_tanatorios": false,
        "mi_proteccion_civil": false,
        "mi_vertederos": false,
    });

    const listaDelimitaciones = reactive({
        "open_street_map": true,
        "orthophoto": false,
        "muni2022": false,
        "dist2022": true,
        "nucleos": true,
        "masa": false,
        "parcela": false,
        "subparce": false,
        "constru": false,
    })

    const listaCallejero = reactive({
        "gdie_g_calles": false,
        "n_policia": false
    })

    const listaLonjasMercadosFerias = reactive({
        "mercado": false,
        "centrocom": false,
        "mercadillos": false,
        "hipermercados": false,
        "galimenta": false,
        "comerespecial": false
    })

    const listaParquesJardines = reactive({
        "parquesocio": false,
        "parques": false
    })

    const listaResiduos = reactive({
        "puntoslim": false,
        "peligrosos": false,
        "vertederos": false,
    })

    const listaCentrosAsistencia = reactive({
        "ssociales": false,
        "inmigrantes": false,
    })

    const listaCentrosSanitarios = reactive({
        "hospital": false,
        "saludmental": false,
        "consultoriosalud": false,
        "centrosalud": false,
        "centroespecialidades": false,
        "drogodependencia": false,
        "saludotros": false,
    })

    const listaCentrosEnsenanza = reactive({
        "educapu": false,
        "educase": false,
        "colegiosmayores": false,
        "univers": false,
    })

    const listaCentrosCulturales = reactive({
        "parroquias": false,
        "plazastoros": false,
        "museos": false,
        "cines": false,
        "galerias": false,
        "centrolectura": false,
        "librerias": false,
        "bibliometro": false,
        "biblimunicipal": false,
        "bibliobus": false,
        "teatros": false,
    })

    const listaInstalacionesDeportivas = reactive({
        "nmcl_deporte": false,
        "nmcl_deporteotros": false,
        "nmcl_imder": false
    })

    const listaBomberos = reactive({
        "bomberos": false,
        "proteccioncivil": false,
    })

    const listaEquipamientoMunicipales = reactive({
        "casas_consistoriales": false,
        "cementerios": false,
        "equipamientos_municipales": false,
    })

    watch(listaEIEL, () => {
        const lista = Object.keys(listaEIEL)
        lista.forEach((e) => {
            const visibility = listaEIEL[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
    });


    watch(listaDelimitaciones, () => {
        const lista = Object.keys(listaDelimitaciones)
        lista.forEach((e) => {
            const visibility = listaDelimitaciones[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        map.value.setLayoutProperty('muni2022_text', 'visibility', listaDelimitaciones.open_street_map ? 'none' : 'visible')
    })


    watch(listaCallejero, () => {
        const lista = Object.keys(listaCallejero)
        lista.forEach((e) => {
            const visibility = listaCallejero[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
    })

    watch(listaLonjasMercadosFerias, () => {
        const lista = Object.keys(listaLonjasMercadosFerias)
        lista.forEach((e) => {
            const visibility = listaLonjasMercadosFerias[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        const isVisible = Object.values(listaLonjasMercadosFerias).some(Boolean);
        listaEIEL.mi_lonja_merca_feria = isVisible;
        listaEIEL.mi_mataderos = isVisible;
    })

    watch(listaParquesJardines, () => {
        const lista = Object.keys(listaParquesJardines)
        lista.forEach((e) => {
            const visibility = listaParquesJardines[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        listaEIEL.mi_parques = listaParquesJardines.parques || listaParquesJardines.parquesocio;
    })

    watch(listaResiduos, () => {
        const lista = Object.keys(listaResiduos)
        lista.forEach((e) => {
            const visibility = listaResiduos[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        const isVisible = Object.values(listaResiduos).some(Boolean);
        listaEIEL.mi_vertederos = isVisible;
    })

    watch(listaCentrosAsistencia, () => {
        const lista = Object.keys(listaCentrosAsistencia)
        lista.forEach((e) => {
            const visibility = listaCentrosAsistencia[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        listaEIEL.mi_centros_asistencia = listaCentrosAsistencia.inmigrantes || listaCentrosAsistencia.ssociales;
    })

    watch(listaCentrosSanitarios, () => {
        const lista = Object.keys(listaCentrosSanitarios)
        lista.forEach((e) => {
            const visibility = listaCentrosSanitarios[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        const isVisible = Object.values(listaCentrosSanitarios).some(Boolean);
        listaEIEL.mi_centros_sanitarios = isVisible;
    })

    watch(listaCentrosEnsenanza, () => {
        const lista = Object.keys(listaCentrosEnsenanza)
        lista.forEach((e) => {
            const visibility = listaCentrosEnsenanza[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        const isVisible = Object.values(listaCentrosEnsenanza).some(Boolean);
        listaEIEL.mi_centros_ensenanza = isVisible;
    })

    watch(listaCentrosCulturales, () => {
        const lista = Object.keys(listaCentrosCulturales)
        lista.forEach((e) => {
            const visibility = listaCentrosCulturales[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        const isVisible = Object.values(listaCentrosCulturales).some(Boolean);
        listaEIEL.mi_centros_culturales = isVisible;
    })

    watch(listaInstalacionesDeportivas, () => {
        const lista = Object.keys(listaInstalacionesDeportivas)
        lista.forEach((e) => {
            const visibility = listaInstalacionesDeportivas[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        const isVisible = Object.values(listaInstalacionesDeportivas).some(Boolean);
        listaEIEL.mi_instalaciones_deportivas = isVisible;
    })

    watch(listaBomberos, () => {
        const lista = Object.keys(listaBomberos)
        lista.forEach((e) => {
            const visibility = listaBomberos[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        const isVisible = Object.values(listaBomberos).some(Boolean);
        listaEIEL.mi_proteccion_civil = isVisible;
    })

    watch(listaEquipamientoMunicipales, () => {
        const lista = Object.keys(listaEquipamientoMunicipales)
        lista.forEach((e) => {
            const visibility = listaEquipamientoMunicipales[e] ? 'visible' : 'none'
            map.value.setLayoutProperty(e, 'visibility', visibility)
        })
        const isVisible = Object.values(listaEquipamientoMunicipales).some(Boolean);

        listaEIEL.mi_casas_consistoriales = isVisible;
        listaEIEL.mi_cementerios = isVisible;
        listaEIEL.mi_edificios_sin_uso = isVisible;
        listaEIEL.mi_tanatorios = isVisible;
    })

    const addMarker = (lng, lat) => {
        if (currentMarker.value) {
            currentMarker.value.remove()
        }
        currentMarker.value = new Marker()
            .setLngLat([lng, lat])
            .addTo(map.value)

        map.value.flyTo({ center: [lng, lat] });
    }


    const addMyLocation = () => {
        navigator.geolocation.getCurrentPosition((position) => {
            const lng = position.coords.longitude
            const lat = position.coords.latitude
            addMarker(lng, lat)
            map.value.flyTo({
                center: [lng, lat],
                zoom: 17
            })
        })
    }

    const loadRegularLayers = () => {
        map.value.on('load', () => {

            var circleYellow = new Image();
            circleYellow.src = '/images/circle_yellow.png';
            circleYellow.onload = function () {
                map.value.addImage('circle_yellow', circleYellow);
                let lista = [
                    "bomberos",
                    "proteccioncivil",
                    "mercado",
                    "centrocom",
                    "mercadillos",
                    "hipermercados",
                    "galimenta",
                    "comerespecial",
                    "parquesocio",
                    "parques",
                    "puntoslim",
                    "peligrosos",
                    "vertederos",
                    "ssociales",
                    "inmigrantes",
                    "hospital",
                    "saludmental",
                    "consultoriosalud",
                    "centrosalud",
                    "centroespecialidades",
                    "drogodependencia",
                    "saludotros",
                    "educapu",
                    "educase",
                    "colegiosmayores",
                    "univers",
                    "parroquias",
                    "plazastoros",
                    "museos",
                    "cines",
                    "galerias",
                    "centrolectura",
                    "librerias",
                    "bibliometro",
                    "biblimunicipal",
                    "bibliobus",
                    "teatros",
                    "nmcl_deporte",
                    "nmcl_deporteotros",
                    "nmcl_imder",
                    "casas_consistoriales",
                    "cementerios",
                    "equipamientos_municipales"
                ];

                lista.forEach((e) => {
                    map.value.addSource(e, {
                        type: "vector",
                        tiles: [`${TEGOLA_DOMAIN}/maps/eiel/${e}/{z}/{x}/{y}.vector.pbf?`],
                        tolerance: 0,
                    });

                    map.value.addLayer({
                        id: e,
                        source: e,
                        "source-layer": e,
                        type: "symbol",
                        layout: {
                            'icon-image': 'circle_yellow',
                            'icon-size': 0.05,
                            'text-field': ['get', 'mi_etiqueta'],
                            'text-size': 12,
                            'text-offset': [0, 1],
                            'text-anchor': 'top',
                            'visibility': 'none'
                        },
                        paint: {
                            'text-color': '#000000',
                            "text-halo-color": "rgba(255,255,255,0.7)",
                            "text-halo-width": 2
                        }
                    });

                    map.value.on('mouseenter', e, function () {
                        map.value.getCanvas().style.cursor = 'pointer';
                    });

                    map.value.on('mouseleave', e, function () {
                        map.value.getCanvas().style.cursor = '';
                    });

                    map.value.on('click', e, function (e) {
                        // console.log("punto", { e })
                        var features = map.value.queryRenderedFeatures(e.point);
                        // console.log({ features })
                        if (!features.length) {
                            return;
                        }

                        const feature = features[0];
                        if (!feature.properties.mi_etiqueta) {
                            Swal.fire({
                                title: 'Error',
                                text: 'No recibo el nombre de este equipamiento. Haga zoom hasta que se muestre.',
                                icon: 'error',
                                showCloseButton: true,
                            });
                            return;
                        }

                        Swal.fire({
                            title: "¿Desea dar de alta este equipamiento?",
                            text: feature.properties.mi_etiqueta,
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
                                Object.assign(payload, {
                                    gid: null,
                                    tipo_equipamiento: opcionSeleccionada,
                                    mi_etiqueta: feature.properties.mi_etiqueta,
                                    lat: e.lngLat.lat,
                                    lng: e.lngLat.lng,
                                    geom: feature.properties.geom,
                                    field_nomecalles: `${feature.source}|${feature.properties.gid}`
                                });
                                showEquipmentForm.value = true;
                            }
                        });
                    });
                })

                lista = [
                    "masa",
                    "parcela",
                    "subparce",
                    "constru",
                    "gdie_g_calles",
                    "n_policia"
                ]

                lista.forEach((e) => {
                    map.value.addSource(e, {
                        type: "vector",
                        tiles: [`${TEGOLA_DOMAIN}/maps/eiel/${e}/{z}/{x}/{y}.vector.pbf?`],
                        tolerance: 0,
                    });
                });

                map.value.addLayer({
                    id: "masa",
                    source: "masa",
                    "source-layer": "masa",
                    minzoom: 13,
                    maxzoom: 15,
                    type: "line",
                    paint: {
                        "line-color": "#999999",
                        "line-width": 1,
                    },
                    'layout': {
                        'visibility': listaDelimitaciones.masa ? 'visible' : 'none'
                    }
                });
                map.value.addLayer({
                    id: "parcela",
                    source: "parcela",
                    minzoom: 15,
                    maxzoom: 20,
                    "source-layer": "parcela",
                    type: "line",
                    paint: {
                        "line-color": "#eeeeee",
                        "line-width": 1,
                    },
                    'layout': {
                        'visibility': listaDelimitaciones.parcela ? 'visible' : 'none'
                    }
                });
                map.value.addLayer({
                    id: "subparce",
                    source: "subparce",
                    minzoom: 17,
                    maxzoom: 18,
                    "source-layer": "subparce",
                    type: "line",
                    paint: {
                        "line-color": "#cccccc",
                        "line-width": 1,
                    },
                    'layout': {
                        'visibility': listaDelimitaciones.subparce ? 'visible' : 'none'
                    }
                });
                map.value.addLayer({
                    id: "constru",
                    source: "constru",
                    minzoom: 18,
                    maxzoom: 20,
                    "source-layer": "constru",
                    type: "line",
                    paint: {
                        "line-color": "#000000",
                        "line-width": 1,
                    },
                    'layout': {
                        'visibility': listaDelimitaciones.constru ? 'visible' : 'none'
                    }
                });
                map.value.addLayer({
                    id: "gdie_g_calles",
                    minzoom: 13,
                    maxzoom: 20,
                    source: "gdie_g_calles",
                    "source-layer": "gdie_g_calles",
                    type: "line",
                    paint: {
                        "line-color": "#eeeeee",
                        "line-width": 2,
                    },
                    'layout': {
                        'visibility': listaCallejero.gdie_g_calles ? 'visible' : 'none'
                    }
                });
                map.value.addLayer({
                    id: "n_policia",
                    source: "n_policia",
                    minzoom: 15,
                    maxzoom: 20,
                    "source-layer": "n_policia",
                    type: "symbol",
                    'layout': {
                        'text-field': ['get', 'numero'],
                        'text-size': 12,
                        'text-offset': [0, 1],
                        'text-anchor': 'top',
                        'visibility': listaCallejero.n_policia ? 'visible' : 'none'
                    },
                    'paint': {
                        'text-color': '#000000',
                        "text-halo-color": "rgba(255,255,255,0.9)",
                        "text-halo-width": 2
                    }
                });
            };

            const addLayerToMap = (map, imageSrc, imageName, sourceName, apiPath, equipmentType) => {
                const image = new Image();
                image.src = imageSrc;
                image.onload = async () => {
                    let data = null;

                    try {
                        const response = await fetch(apiPath, {
                            headers: {
                                'Authorization': `Bearer ${userStore.user.token}`,
                                'Accept': 'application/json'
                            }
                        })
                        data = await response.json();
                    } catch (error) {
                        console.error('Error:', error)
                        return;
                    }

                    map.value.addImage(imageName, image);
                    map.value.addSource(sourceName, {
                        type: "geojson",
                        data: data,
                    });

                    map.value.addLayer({
                        id: sourceName,
                        source: sourceName,
                        type: "symbol",
                        layout: {
                            'icon-image': imageName,
                            'icon-size': 0.5,
                            'icon-allow-overlap': true,
                            'text-field': ['get', 'mi_etiqueta'],
                            'text-size': 12,
                            'text-offset': [0, 1],
                            'text-anchor': 'top',
                            'visibility': 'none',
                            'text-overlap': 'always',
                            'text-allow-overlap': true
                        },
                        paint: {
                            'text-color': [
                                'case',
                                ['get', 'completo'],
                                '#0000ff',
                                '#ff0000'
                            ],
                            "text-halo-color": "rgba(255,255,255,0.7)",
                            "text-halo-width": 2,                            
                        }
                    });

                    map.value.on('mouseenter', sourceName, function () {
                        map.value.getCanvas().style.cursor = 'pointer';
                    });

                    map.value.on('mouseleave', sourceName, function () {
                        map.value.getCanvas().style.cursor = '';
                    });

                    map.value.on('click', sourceName, function (e) {
                        var features = map.value.queryRenderedFeatures(e.point);
                        if (!features.length) {
                            return;
                        }

                        const feature = features[0];
                        if (!feature.properties.mi_etiqueta) {
                            Swal.fire({
                                title: 'Error',
                                text: 'No recibo el nombre de este equipamiento. Haga zoom hasta que se muestre.',
                                icon: 'error',
                                showCloseButton: true,
                            });
                            return;
                        }

                        Swal.fire({
                            title: "¿Desea modificar este equipamiento?",
                            text: feature.properties.mi_etiqueta,
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText: 'Modificar',
                            cancelButtonText: 'Cancelar',
                            html: '<button id="thirdButton" class="swal2-confirm swal2-styled" style="display: inline-block; background-color: red;">Desplazar</button>',
                            preConfirm: () => {
                                return new Promise((resolve) => {
                                    resolve();
                                });
                            },
                            didOpen: () => {
                                const thirdButton = Swal.getPopup().querySelector('#thirdButton');
                                thirdButton.addEventListener('click', () => {
                                    // currentMarker.value.remove();
                                    currentMarker.value.setDraggable(true);
                                    console.log('gid', feature.properties.gid.toString());
                                    console.log('mi_etiqueta', feature.properties.mi_etiqueta);
                                    const { gid, tabla } = feature.properties;
                                    // console.log('tipo', feature.properties);

                                    currentMarker.value.on('dragend', async () => {
                                        const { lng, lat } = currentMarker.value.getLngLat();                                        
                                        const response = await fetch(`/api/helpers/move/${gid}/${tabla}?lat=${lat}&lng=${lng}`, {
                                            method: 'PUT',
                                            headers: {
                                                'Content-Type': 'application/json',
                                                'Authorization': `Bearer ${userStore.user.token}`,
                                            }
                                        })
                                        currentMarker.value.remove();
                                        if (!response.ok) {
                                            let error_message = 'No se ha podido mover el equipamiento'
                                            if (response.status === 400) {
                                                error_message = "Diferente municipio y poblamiento. No se puede mover el equipamiento a esa localización"
                                            }
                                            if (response.status === 402) {
                                                error_message = "Acción no permitida para rol Ayuntamiento"
                                            }
                                            Swal.fire({
                                                title: 'Error',
                                                text: error_message,
                                                icon: 'error',
                                                showCloseButton: true,
                                            });
                                            return;
                                        }

                                        fetch(apiPath, {
                                            method: 'GET',
                                            headers: {
                                                'Authorization': `Bearer ${userStore.user.token}`,
                                                'Accept': 'application/json'
                                            }
                                        })
                                            .then(response => response.json())
                                            .then(data => {
                                                map.value.getSource(sourceName).setData(data);
                                                Swal.fire({
                                                    title: 'Éxito',
                                                    text: 'El equipamiento se ha movido correctamente',
                                                    icon: 'success',
                                                    showCloseButton: true,
                                                    timer: 1500,
                                                });
                                            })
                                            .catch(error => console.error('Error:', error))

                                    });

                                    Swal.close();

                                });
                            }
                        }).then((result) => {
                            if (result.isConfirmed) {
                                Object.assign(payload, {
                                    gid: feature.properties.gid.toString(),
                                    tipo_equipamiento: equipmentType,
                                    mi_etiqueta: feature.properties.mi_etiqueta,
                                    lat: null,
                                    lng: null,
                                    geom: null,
                                    field_nomecalles: null,
                                });
                                showEquipmentForm.value = true;
                            }
                        });
                    });
                }
            }

            addLayerToMap(map, '/images/ce.png', 'ceImage', 'mi_cementerios', '/api/cemeteries/', 'CE');
            addLayerToMap(map, '/images/as.png', 'asImage', 'mi_centros_asistencia', '/api/assistance-centers/', 'AS');
            addLayerToMap(map, '/images/cc.png', 'ccImage', 'mi_casas_consistoriales', '/api/townhalls/', 'CC');
            addLayerToMap(map, '/images/pj.png', 'pjImage', 'mi_parques', '/api/parks/', 'PJ');
            addLayerToMap(map, '/images/en.png', 'enImage', 'mi_centros_ensenanza', '/api/educational-centers/', 'EN');
            addLayerToMap(map, '/images/sa.png', 'saImage', 'mi_centros_sanitarios', '/api/medical-centers/', 'SA');
            addLayerToMap(map, '/images/cu.png', 'cuImage', 'mi_centros_culturales', '/api/cultural-centers/', 'CU');
            addLayerToMap(map, '/images/su.png', 'suImage', 'mi_edificios_sin_uso', '/api/unused-public-buildings/', 'SU');
            addLayerToMap(map, '/images/id.png', 'idImage', 'mi_instalaciones_deportivas', '/api/sports-facilities/', 'ID');
            addLayerToMap(map, '/images/lm.png', 'lmImage', 'mi_lonja_merca_feria', '/api/markets/', 'LM');
            addLayerToMap(map, '/images/mt.png', 'mtImage', 'mi_mataderos', '/api/slaughterhouses/', 'MT');
            addLayerToMap(map, '/images/ta.png', 'taImage', 'mi_tanatorios', '/api/mortuaries/', 'TA');
            addLayerToMap(map, '/images/ip.png', 'ipImage', 'mi_proteccion_civil', '/api/civil-protections/', 'IP');
            addLayerToMap(map, '/images/vt.png', 'vtImage', 'mi_vertederos', '/api/landfills/', 'VT');

        });
    }

    return {
        TEGOLA_DOMAIN,
        showMenu,
        showEquipmentForm,
        streetSearchInput,
        clearStreetSearchInput,
        payload,
        map,
        center,
        mi_etiqueta,
        addMarker,
        currentMarker,
        addMyLocation,
        listaEIEL,
        listaDelimitaciones,
        listaCallejero,
        listaLonjasMercadosFerias,
        listaParquesJardines,
        listaResiduos,
        listaCentrosAsistencia,
        listaCentrosSanitarios,
        listaCentrosEnsenanza,
        listaCentrosCulturales,
        listaInstalacionesDeportivas,
        listaBomberos,
        listaEquipamientoMunicipales,
        loadRegularLayers,
        tipo_equipamiento,
    }
});
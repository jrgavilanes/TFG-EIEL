<script setup>
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
const route = useRoute();

// import { getInfo } from '@/services/equipmentService.js';



console.log(route.params);

const { lat, lng, mi_etiqueta, tipo_equipamiento, geom, field_nomecalles } = route.params

// import EquipmentCreate from '@/components/EquipmentCreate.vue';
import CementerioForm from '@/components/polls/CementerioForm.vue';



onMounted(() => {
    console.log('mounted');
    console.log(lat, lng, mi_etiqueta, tipo_equipamiento);
});

</script>

<template>
    <div class="px-4 pb-8">
        <CementerioForm v-if="tipo_equipamiento === 'CE'" :lat="Number(lat)" :lng="Number(lng)" :mi_etiqueta="mi_etiqueta"
            :tipo_equipamiento="tipo_equipamiento" :geom="geom" :field_nomecalles="field_nomecalles" />

    </div>
</template>
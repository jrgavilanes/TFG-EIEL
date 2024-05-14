<script setup>
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
const route = useRoute();

console.log(route.params);

const { tipo_equipamiento, gid } = route.params


// import EquipmentCreate from '@/components/EquipmentCreate.vue';
import CementerioForm from '@/components/polls/CementerioForm.vue';



onMounted(() => {
    console.log('mounted update equipment');
    console.log(tipo_equipamiento, gid);
});

</script>

<template>
    <div class="px-4 pb-8">
        <CementerioForm v-if="tipo_equipamiento === 'CE'" :gid="gid" :tipo_equipamiento="tipo_equipamiento" />
    </div>
</template>
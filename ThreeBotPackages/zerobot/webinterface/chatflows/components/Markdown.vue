<template>
  <div v-html="html"></div>
</template>

<script>  
  module.exports = {    
    props: {payload: Object},
    computed: {
      html () {
        return marked(this.payload.msg)
      }
    }
  }
</script>

<style scoped>
 code {
   padding: 7px;
   margin: 10px 0px;
 }

 h1, h2, h3 {
   font-weight: 600 !important;
   font-family: sans-serif !important;
 }
</style>
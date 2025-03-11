<template>
    <div>

        <div class="wrapper">
            <nav class="navbar">
                    <router-link to="/create_product" class="logo__text">Onephrase.tech</router-link>
                    <router-link to="/files" class="nav-link">Файлы</router-link>
                </nav>
            <div class="container">
 
                <h2>Список файлов</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Название файла</th>
                            <th>Действие</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="file in files" :key="file">
                            <td>{{ file }}</td>
                            <td>
                                <button @click="downloadFile(file)">Скачать</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            files: []
        };
    },
    mounted() {
        this.fetchFiles();
    },
    methods: {
        async fetchFiles() {
            try {
                const response = await fetch(`api/products/xlsx_files`);
                const data = await response.json();
                this.files = data.files;
            } catch (error) {
                console.error("Ошибка загрузки списка файлов:", error);
            }
        },
        downloadFile(filename) {
            window.location.href = `api/products/download_xlsx/${filename}`;
        }
    }
};
</script>

<style>
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    padding: 10px 20px;
    background-color: #333;
    color: white;
}

.nav-link {
    color: white;
    text-decoration: none;
    margin-right: 20px;
}

.wrapper {
    width: 1000px;
    display: flex;
    justify-content: center;
    /* align-items: center; */
    flex-direction: column;
}

.container {
    max-width: 600px;
    margin: 20px auto;
    padding: 20px;
    background: #f9f9f9;
    border-radius: 5px;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 10px;
    border: 1px solid #ddd;
    text-align: left;
}

button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 5px 10px;
    cursor: pointer;
    border-radius: 3px;
}

button:hover {
    background-color: #0056b3;
}
</style>

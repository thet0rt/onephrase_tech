<template>
    <div>
        <nav class="navbar">
            <h1 class="logo__text">Onephrase.tech</h1>
        </nav>
        <div class="main__content">
            <div class="container__reset">
                <button class="button__reset" @click="resetForm">Сбросить</button>
            </div>
            <div class="container__title">
                <h1 class="title">>><br>Создать новый товар</h1>
            </div>
            <div class="container__input_phrase">
                <h4 class="input__phrase__name">введите фразу</h4>
                <input class="input__phrase" type="text" v-model="phrase" placeholder="Введите фразу">
            </div>
            <div class="container__input_phrase">
                <h4 class="input__phrase__name">введите номер дизайна</h4>
                <input class="input__phrase" type="text" v-model="designNumber" placeholder="введите номер дизайна">
            </div>
            <div class="container__input_phrase">
                <h4 class="input__phrase__name">введите категории</h4>
                <input class="input__category" type="text" v-model="categories[0]" placeholder="категория">
                <input class="input__category" type="text" v-model="categories[1]" placeholder="категория">
                <input class="input__category" type="text" v-model="categories[2]" placeholder="категория">
            </div>
            <div class="components">
                <div v-for="(item, index) in images" :key="index" class="img__button">
                    <img class="component_image" :src="item.src" alt="">
                    <button class="button__change" @click="openModal(index)">изменить</button>
                </div>
            </div>
            <div class="getfile__container">
                <p class="phrase__counter">количество фраз ({{ phraseCount }})</p>
                <button class="button_bottom" @click="addPhrase">Добавить ещё фразу</button>
                <button class="button_bottom" @click="generateFile">Сгенерировать файл</button>
            </div>
        </div>

        <!-- Модальное окно -->
        <div v-if="isModalOpen" class="modal">
            <div class="modal__content">
                <span class="close" @click="closeModal">&times;</span>
                <canvas v-if="isModalOpen" ref="canvas" class="modal__canvas" @mousedown="startDragging"
                    @mousemove="dragText" @mouseup="stopDragging" @mouseleave="stopDragging"></canvas>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            phrase: "",
            designNumber: "",
            categories: ["", "", ""],
            phraseCount: 0,
            images: [
                { src: "hoodie.png", bigSrc: "hoodie_big.png" },
                { src: "sweetshirt.png", bigSrc: "sweetshirt_big.png" },
                { src: "hoodie.png", bigSrc: "hoodie_big.png" },
                { src: "longsleeve.png", bigSrc: "longsleeve_big.png" },
                { src: "t_shirt_basic.png", bigSrc: "t_shirt_basic_big.png" },
                { src: "t_shirt_true_over.png", bigSrc: "t_shirt_true_over_big.png" }
            ],
            isModalOpen: false,
            selectedImage: "",
            textX: 100,
            textY: 100,
            isDragging: false,
            canvas: null,
            ctx: null
        };
    },
    methods: {
        resetForm() {
            this.phrase = "";
            this.designNumber = "";
            this.categories = ["", "", ""];
            this.phraseCount = 0;
        },
        addPhrase() {
            this.phraseCount++;
        },
        generateFile() {
            alert("Файл сгенерирован!");
        },
        openModal(index) {
            this.selectedImage = this.images[index].bigSrc;
            this.isModalOpen = true;
            this.$nextTick(() => {
                this.canvas = this.$refs.canvas;
                console.log("openModal: Canvas is", this.canvas);

                if (this.canvas) {
                    this.ctx = this.canvas.getContext("2d");
                    if (this.ctx) {
                        console.log("Context is available!");
                        this.loadImageAndDraw();  // Теперь загружаем изображение перед рисованием
                    }
                }
            });
        },

        // Метод для загрузки изображения и рисования на холсте
        loadImageAndDraw() {
            const img = new Image();
            img.onload = () => {
                // Отображаем изображение на холсте
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);  // Рисуем изображение, растягивая на весь холст
                this.drawCanvas();  // Рисуем текст после изображения
            };
            img.src = this.selectedImage;  // Загружаем изображение по URL
        },

        closeModal() {
            this.isModalOpen = false;
        },
        drawCanvas() {
            this.canvas = this.$refs.canvas;
            this.ctx = this.canvas.getContext("2d");
            const img = new Image();
            img.src = this.selectedImage;
            img.onload = () => {
                this.canvas.width = img.width;
                this.canvas.height = img.height;
                this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
                this.drawText();
            };
        },
        drawText() {
            if (!this.ctx) return;
            console.log(`Drawing text at: (${this.textX}, ${this.textY})`);
            this.ctx.font = "30px Arial";
            this.ctx.fillStyle = "black";
            this.ctx.fillText(this.phrase, this.textX, this.textY);
        },
        // Метод для рисования текста на холсте
        // drawCanvas() {
        //     this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        //     this.ctx.fillStyle = "#000000";
        //     this.ctx.font = "30px Arial";
        //     this.ctx.fillText("Hello World", this.textX, this.textY);
        //     console.log(`Drawing text at: (${this.textX}, ${this.textY})`);
        // },

        // Метод для начала перетаскивания текста
        startDragging(e) {
            const mouseX = e.offsetX;
            const mouseY = e.offsetY;
            if (this.isMouseOverText(mouseX, mouseY)) {
                this.isDragging = true;
                this.dragOffsetX = mouseX - this.textX;
                this.dragOffsetY = mouseY - this.textY;
                console.log("Dragging started");
            }
        },

        // Метод для перемещения текста при перетаскивании
        dragText(e) {
            if (this.isDragging) {
                this.textX = e.offsetX - this.dragOffsetX;
                this.textY = e.offsetY - this.dragOffsetY;
                this.drawCanvas();
            }
        },

        // Метод для завершения перетаскивания
        stopDragging() {
            this.isDragging = false;
            console.log("Dragging stopped");
        },

        // Проверяем, находится ли курсор мыши на тексте
        isMouseOverText(mouseX, mouseY) {
            return (
                mouseX >= this.textX &&
                mouseX <= this.textX + this.ctx.measureText("Hello World").width &&
                mouseY >= this.textY - 30 &&
                mouseY <= this.textY
            );
        },
        handleMouseDown(event) {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = event.clientX - rect.left;
            const mouseY = event.clientY - rect.top;
            const textWidth = this.ctx.measureText(this.phrase).width;
            const textHeight = 30; // высота шрифта

            if (
                mouseX >= this.textX &&
                mouseX <= this.textX + textWidth &&
                mouseY >= this.textY - textHeight &&
                mouseY <= this.textY
            ) {
                this.isDragging = true;
                this.offsetX = mouseX - this.textX;
                this.offsetY = mouseY - this.textY;
            }
        },
        handleMouseMove(event) {
            if (this.isDragging) {
                const rect = this.canvas.getBoundingClientRect();
                const mouseX = event.clientX - rect.left;
                const mouseY = event.clientY - rect.top;

                this.textX = mouseX - this.offsetX;
                this.textY = mouseY - this.offsetY;
                this.redrawCanvas();
            }
        },
        handleMouseUp() {
            this.isDragging = false;
        },
        redrawCanvas() {
            // Очищаем canvas
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            // Рисуем изображение
            const img = new Image();
            img.src = this.selectedImage;
            img.onload = () => {
                this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
                this.drawText();
            };
        },
    },
    mounted() {
        this.$nextTick(() => {
            this.canvas = this.$refs.canvas;
            if (this.canvas) {
                this.ctx = this.canvas.getContext("2d");
                if (this.ctx) {
                    this.canvas.addEventListener("mousedown", this.handleMouseDown.bind(this));
                    this.canvas.addEventListener("mousemove", this.handleMouseMove.bind(this));
                    this.canvas.addEventListener("mouseup", this.handleMouseUp.bind(this));
                }
            }
        });
    },
    beforeDestroy() {
        if (this.canvas) {
            this.canvas.removeEventListener("mousedown", this.handleMouseDown);
            this.canvas.removeEventListener("mousemove", this.handleMouseMove);
            this.canvas.removeEventListener("mouseup", this.handleMouseUp);
        }
    }
};
</script>

<style scoped>
@import '@/assets/styles.css';

.modal__content {
    position: relative;
    background-color: #ffffff;
    padding: 20px;
    border-radius: 10px;
    /* Обрамление вокруг изображения */
    border: 1px solid black;
}

.modal__canvas {
    display: block;
    border: 2px solid #000000;
    /* Белое обрамление */
    max-width: 90%;
    /* Чтобы картинка не выходила за пределы окна */
    max-height: 90%;
    /* Ограничиваем высоту */
}

.modal {
    position: fixed;
    /* Фиксируем модальное окно */
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(255, 255, 255, 0.5);
    /* Прозрачный фон */
    /* border: 10px solid black; */
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    /* Чтобы окно было поверх других элементов */
}
</style>
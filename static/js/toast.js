const Toast = {
    init() {
        this.hideTimeout = null;

        this.el = document.createElement('div');
        this.el.className = 'toast';
        document.body.appendChild(this.el);
    },

    show(message, state) {
        clearTimeout(this.hideTimeout);

        this.el.textContent = message;
        this.el.className = 'toast toast--visible';

        if (state) {
            this.el.classList.add(`toast--${state}`)
        }

        this.hideTimeout = setTimeout(() => {
            this.el.classList.remove('toast--visible');
            window.sessionStorage.setItem('toast', 'null');
        }, 2000);
    },

    showAfterReload(message, state) {
        try {
            window.sessionStorage.setItem('toast', state);
            window.sessionStorage.setItem('msg', message);
        } catch (e) {
            console.log(e)
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Toast.init()
    console.log('toast initialized')
    try {
        let state = window.sessionStorage.getItem('toast')
        if (state !== 'null') {
            console.log('state was not null')
            let msg = window.sessionStorage.getItem('msg');
            Toast.show(msg, state)
        }
    } catch (e) {
        console.log(e)
    }
});
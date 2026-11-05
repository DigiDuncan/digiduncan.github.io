var saved_language = localStorage.getItem('language') || 'en';

function lang_switch(new_lang) {
    localStorage.setItem('language', new_lang);
    saved_language = new_lang;

    const en_elements = document.getElementsByClassName('lang-en');
    for (const element of en_elements) {
        element.style.display = new_lang === 'en' ? "flex" : "none"
    }

    const tp_elements = document.getElementsByClassName('lang-tp');
    for (const element of tp_elements) {
        element.style.display = new_lang === 'tp' ? "flex" : "none"
    }
}

function lang_button() {
    var new_lang = saved_language === 'en' ? 'tp' : 'en';
    lang_switch(new_lang);
}

const lang_button_elements = document.getElementsByClassName('button-lang');
for (const element of lang_button_elements) {
        element.addEventListener('click', lang_button);
    }

lang_switch(saved_language);

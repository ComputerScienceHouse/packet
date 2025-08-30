$(document).ready(function () {
    let photos = Array.from(document.querySelectorAll('.eval-user-img'))

    top.onclick = function (e) {
        let tsib = e.target.previousElementSibling
        if (tsib != null) {
            if (tsib.classList.contains('eval-user-img')) {
                return;
            }
        }
        if (e.target.classList.contains('eval-user-img')) {
            return;
        }
        document.querySelector('#zoom-photo').remove()
    }

    photos.forEach((photo) => {
        photo.addEventListener('click', (e) => {
            let other = document.querySelector('#zoom-photo')
            if (other != null) {
                other.remove()
            }
            photo.insertAdjacentHTML('afterend', `
                <div id="zoom-photo" style="position: fixed; z-index: 1050; display: block">
                    <img class="eval-user-img"
                        alt=${photo.alt}
                        src=${photo.src}
                        style="max-width: 200px; max-height: 200px; border: 1px solid #666"
                        >
                </div>
                `)
            e.preventDefault();
        })
    })

})
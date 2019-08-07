requestPermission();

function requestPermission() {
    Notification.requestPermission().then((permission) => {
        if (permission === 'granted') {
            console.log('Notification permission granted.');
            getToken();
            onTokenRefresh()
        } else {
            console.log('Unable to get permission to notify.');
        }
    });
}

function getToken() {
    messaging.getToken().then((currentToken) => {
        if (currentToken) {
            sendTokenToServer(currentToken);
            console.log(currentToken)
        } else {
            console.log('No Instance ID token available. Request permission to generate one.');
            requestPermission()
        }
    }).catch((err) => {
        console.log('An error occurred while retrieving token. ', err);
    });
}

function onTokenRefresh() {
    messaging.onTokenRefresh(() => {
        messaging.getToken().then((refreshedToken) => {
            console.log('Token refreshed.');
            setTokenSentToServer(false);
            sendTokenToServer(refreshedToken)
        }).catch((err) => {
            console.log('Unable to retrieve refreshed token ', err);
        });
    });
}

function sendTokenToServer(currentToken) {
    if (!isTokenSentToServer()) {
        console.log('Sending token to server...');
        $.ajax({
            url: "/api/v1/subscribe/",
            method: "POST",
            data: {
                token: currentToken
            },
            success: function (data) {
                console.log(data);
                setTokenSentToServer(true);
            }
        });
    } else {
        console.log('Token already sent to server so won\'t send it again ' +
            'unless it changes');
    }
}

function setTokenSentToServer(sent) {
    window.localStorage.setItem('sentToServer', sent ? '1' : '0');
}

function isTokenSentToServer() {
    return window.localStorage.getItem('sentToServer') === '1';
}

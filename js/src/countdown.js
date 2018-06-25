"use strict";

function countdown(countdown_url, csrf_token){
    $.ajax(
        countdown_url, {
        "headers": {"X-CSRFToken": csrf_token}
    }).done(data => {
        let start = data.date_start; // Used for shorthand to increase readability
        let end = data.date_end;

        const startjam = new Date(Date.UTC( // As the months, days, etc. all start from 0 we need to negate 1
            start.year, start.month-1, start.day-1,
            start.hours-1, start.minutes-1, start.seconds-1
        ));
        const endjam = new Date(Date.UTC(
            end.year, end.month-1, end.day-1,
            end.hours-1, end.minutes-1, end.seconds-1
        ));

        const now = Date.now();
        let goal;
        if (now + 1000 < endjam.getTime()) { // Only do anything if the jam hasn't ended
            console.log("good");
            UIkit.notification( // Spawn the notification
                {
                    "message": ""
                    + "<div class='uk-text-center'>"
                    + "    <span id=\"countdown-title\" class=\"uk-text-center\">"
                    + "        <a href=\"/info/jams\">Code Jam</a> Countdown"
                    + "    </span>"
                    + "    <p class='uk-text-large' id=\"countdown-remaining\">...</p>"
                    + "<small style='font-size: 0.6em;'>(Tap/click to dismiss)</small>"
                    + "</div>",
                    "pos": "bottom-right",
                    "timeout": endjam - now
                }
            );

            const heading = document.getElementById("countdown-title");

            if (now > startjam.getTime()) { // Jam's already started
                heading.innerHTML = "Current <a href=\"/info/jams\">code jam</a> ends in...";
                goal = endjam.getTime();
            } else {
                heading.innerHTML = "Next <a href=\"/info/jams\">code jam</a> starts in...";
                goal = startjam.getTime();
            }

            const refreshCountdown = setInterval(() => { // Create a repeating task
                let delta = goal - Date.now(); // Time until the goal is met

                if (delta <= 1000) { // Goal has been met, best reload
                    clearInterval(refreshCountdown);
                    return location.reload();
                }

                let days = Math.floor(delta / (24 * 60 * 60 * 1000));
                delta -= days * (24 * 60 * 60 * 1000);

                let hours = Math.floor(delta / (60 * 60 * 1000));
                delta -= hours * (60 * 60 * 1000);

                let minutes = Math.floor(delta / (60 * 1000));
                delta -= minutes * (60 * 1000);

                let seconds = Math.floor(delta / 1000);

                if (days < 10) {
                    days = `0${days}`;
                }

                if (hours < 10) {
                    hours = `0${hours}`;
                }

                if (minutes < 10) {
                    minutes = `0${minutes}`;
                }

                if (seconds < 10) {
                    seconds = `0${seconds}`;
                }

                try {
                    document.getElementById("countdown-remaining").innerHTML = `${days}:${hours}:${minutes}:${seconds}`;
                } catch (e) { // Notification was probably closed, so we can stop counting
                    return clearInterval(refreshCountdown);
                }
            }, 500);
        }
    });
};

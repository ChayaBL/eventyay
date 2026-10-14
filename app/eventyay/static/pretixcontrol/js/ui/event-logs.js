(function () {
    "use strict";

    var resultsSelector = ".event-log-results";
    var requestVersion = 0;
    var activeRequest = null;

    function getResults(html) {
        var parsed = new DOMParser().parseFromString(html, "text/html");
        return parsed.querySelector(resultsSelector);
    }

    function loadResults(url, updateHistory) {
        var target = new URL(url, window.location.href);

        if (target.origin !== window.location.origin) {
            window.location.href = target.href;
            return;
        }

        var version = ++requestVersion;
        if (activeRequest) {
            activeRequest.abort();
        }
        activeRequest = new AbortController();

        fetch(target.href, {
            credentials: "same-origin",
            headers: { "X-Requested-With": "XMLHttpRequest" },
            signal: activeRequest.signal
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Event log request failed");
                }
                return response.text();
            })
            .then(function (html) {
                if (version !== requestVersion) {
                    return;
                }

                var newResults = getResults(html);
                var currentResults = document.querySelector(resultsSelector);

                if (!newResults || !currentResults) {
                    window.location.href = target.href;
                    return;
                }

                currentResults.replaceWith(newResults);
                if (updateHistory) {
                    window.history.pushState({}, "", target.href);
                }
            })
            .catch(function (error) {
                if (error.name === "AbortError" || version !== requestVersion) {
                    return;
                }
                window.location.href = target.href;
            });
    }

    document.addEventListener("submit", function (event) {
        var form = event.target.closest(".event-log-search-form");
        if (!form) {
            return;
        }

        event.preventDefault();
        var target = new URL(form.action || window.location.href, window.location.href);
        var params = new URLSearchParams(new FormData(form));
        params.delete("page");

        // Keep the selected page size when the form is submitted.
        var currentPageSize = new URL(window.location.href).searchParams.get("page_size");
        if (currentPageSize && !params.has("page_size")) {
            params.set("page_size", currentPageSize);
        }

        target.search = params.toString();
        loadResults(target.href, true);
    });

    document.addEventListener("click", function (event) {
        var anchor = event.target.closest(
            ".event-log-results .pagination a, .event-log-results a[href*='page_size='], .event-log-clear-search"
        );
        if (!anchor || !anchor.hasAttribute("href") || !anchor.getAttribute("href")) {
            return;
        }

        var target = new URL(anchor.href, window.location.href);
        if (target.origin !== window.location.origin) {
            return;
        }

        if (anchor.matches(".event-log-clear-search")) {
            var currentPageSize = new URL(window.location.href).searchParams.get("page_size");
            if (currentPageSize && !target.searchParams.has("page_size")) {
                target.searchParams.set("page_size", currentPageSize);
            }
        }

        event.preventDefault();
        loadResults(target.href, true);
    });

    window.addEventListener("popstate", function () {
        if (!document.querySelector(resultsSelector)) {
            return;
        }
        loadResults(window.location.href, false);
    });
})();

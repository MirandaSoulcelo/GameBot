class EJS_STORAGE {
    constructor(dbName, storeName) {
        this.dbName = dbName;
        this.storeName = storeName;
    }
    addFileToDB(key, add) {
        (async () => {
            if (key === "?EJS_KEYS!") return;
            let keys = await this.get("?EJS_KEYS!");
            if (!keys) keys = [];
            if (add) {
                if (!keys.includes(key)) keys.push(key);
            } else {
                const index = keys.indexOf(key);
                if (index !== -1) keys.splice(index, 1);
            }
            this.put("?EJS_KEYS!", keys);
        })();
    }
    get(key) {
        return new Promise((resolve, reject) => {
            if (!window.indexedDB) return resolve();
            let openRequest = indexedDB.open(this.dbName, 1);
            openRequest.onerror = () => resolve();
            openRequest.onsuccess = () => {
                let db = openRequest.result;
                let transaction = db.transaction([this.storeName], "readwrite");
                let objectStore = transaction.objectStore(this.storeName);
                let request = objectStore.get(key);
                request.onsuccess = (e) => {
                    resolve(request.result);
                };
                request.onerror = () => resolve();
            };
            openRequest.onupgradeneeded = () => {
                let db = openRequest.result;
                if (!db.objectStoreNames.contains(this.storeName)) {
                    db.createObjectStore(this.storeName);
                };
            };
        });
    }
    put(key, data) {

    return new Promise((resolve, reject) => {

        if (!window.indexedDB)
            return resolve();

        let openRequest =
            indexedDB.open(this.dbName, 1);

        openRequest.onerror = () => {};

        openRequest.onsuccess = () => {

            let db =
                openRequest.result;

            let transaction =
                db.transaction(
                    [this.storeName],
                    "readwrite"
                );

            let objectStore =
                transaction.objectStore(
                    this.storeName
                );

            let request =
                objectStore.put(
                    data,
                    key
                );

            request.onerror =
                () => resolve();

            request.onsuccess =
                async () => {

                this.addFileToDB(
                    key,
                    true
                );

                console.log(
                    "[EJS] Arquivo salvo:",
                    key
                );

                //
                // CLOUD SAVE
                //
                try {

                    if (
                        key.endsWith(".srm") ||
                        key.endsWith(".sav")
                    ) {

                        console.log(
                            "[SAVE] Save detectado!"
                        );

                        let base64 = "";

                        //
                        // formato mais comum
                        //
                        if (data?.data) {

                            const uint8 =
                                new Uint8Array(
                                    data.data
                                );

                            let binary = "";

                            uint8.forEach(b => {

                                binary +=
                                    String.fromCharCode(b);
                            });

                            base64 =
                                btoa(binary);
                        }

                        //
                        // fallback
                        //
                        else if (
                            data instanceof Uint8Array
                        ) {

                            let binary = "";

                            data.forEach(b => {

                                binary +=
                                    String.fromCharCode(b);
                            });

                            base64 =
                                btoa(binary);
                        }

                        if (base64) {

                            console.log(
                                "[SAVE] Enviando pro backend..."
                            );

                            const response =
                                await fetch(
                                    `/save/${window.GAME}`,
                                    {
                                        method: "POST",

                                        headers: {
                                            "Content-Type":
                                                "application/json"
                                        },

                                        body: JSON.stringify({

                                            user_id:
                                                window.USER_ID,

                                            data:
                                                base64
                                        })
                                    }
                                );

                            console.log(
                                "[SAVE] Status:",
                                response.status
                            );

                            console.log(
                                "[SAVE] Save enviado!"
                            );
                        }
                    }

                } catch(e) {

                    console.error(
                        "[SAVE] Erro upload:",
                        e
                    );
                }

                resolve();
            };
        };

        openRequest.onupgradeneeded =
            () => {

            let db =
                openRequest.result;

            if (
                !db.objectStoreNames.contains(
                    this.storeName
                )
            ) {

                db.createObjectStore(
                    this.storeName
                );
            }
        };
    });
}
    remove(key) {
        return new Promise((resolve, reject) => {
            if (!window.indexedDB) return resolve();
            let openRequest = indexedDB.open(this.dbName, 1);
            openRequest.onerror = () => {};
            openRequest.onsuccess = () => {
                let db = openRequest.result;
                let transaction = db.transaction([this.storeName], "readwrite");
                let objectStore = transaction.objectStore(this.storeName);
                let request2 = objectStore.delete(key);
                this.addFileToDB(key, false);
                request2.onsuccess = () => resolve();
                request2.onerror = () => {};
            };
            openRequest.onupgradeneeded = () => {
                let db = openRequest.result;
                if (!db.objectStoreNames.contains(this.storeName)) {
                    db.createObjectStore(this.storeName);
                };
            };
        });
    }
    getSizes() {
        return new Promise(async (resolve, reject) => {
            if (!window.indexedDB) resolve({});
            const keys = await this.get("?EJS_KEYS!");
            if (!keys) return resolve({});
            let rv = {};
            for (let i = 0; i < keys.length; i++) {
                const result = await this.get(keys[i]);
                if (!result || !result.data || typeof result.data.byteLength !== "number") continue;
                rv[keys[i]] = result.data.byteLength;
            }
            resolve(rv);
        })
    }
}

class EJS_DUMMYSTORAGE {
    constructor() {}
    addFileToDB() {
        return new Promise(resolve => resolve());
    }
    get() {
        return new Promise(resolve => resolve());
    }
    put() {
        return new Promise(resolve => resolve());
    }
    remove() {
        return new Promise(resolve => resolve());
    }
    getSizes() {
        return new Promise(resolve => resolve({}));
    }
}

window.EJS_STORAGE = EJS_STORAGE;
window.EJS_DUMMYSTORAGE = EJS_DUMMYSTORAGE;

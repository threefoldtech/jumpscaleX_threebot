import { ExternalView } from "../external";
import { admin } from "../../services/admin";


export default class CapacityView extends ExternalView {
    constructor(app, name) {
        super(app, name);
    }

    showIframe() {
        admin.get_explorer().then((data) => {
            const explorer = data.json();
            let url = explorer.url;

            if (!url.startsWith('http')) {
                url = `https://${url}`;
            }

            this.externalIframe.show();
            this.externalIframe.showProgress({ type: "icon" });
            this.externalIframe.load(url);
        })
    }
}

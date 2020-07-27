import { JetView, plugins } from "webix-jet";
import SolutionDetailsView from './SolutionDetails';
import { solutions } from '../../services/deployedSolutions';


export class BaseView extends JetView {
    constructor(app, name, chat, logo) {
        super(app, name);
        this.logo = logo || "3bot.png";
        this.chat = chat;
    }
    config() {

        const migrationView = {
            id: "migrateView",
            cols: [
                {
                    view: "template",
                    hidden: true,
                    id: "migratMessage",
                    template: `<h2 class="message_migration">The explporer has been upgraded, so you need to initialize the migration of your old reservations to be able to use them. To migrate please click on the bellow button.</h2>`,
                    css: 'message_migration',
                    align: "center",
                    borderless: true,
                },
                {
                    view: "button",
                    id: "btnMigrate",
                    hidden: true,
                    value: "Migrate",
                    width: 170,
                    height: 70,
                    css: "webix_primary btnCreateNew",
                    click: function () {
                        solutions.migrate().then(data => {
                            this.app.refresh()
                        });
                    }
                }
            ]
        }

        const logo = {
            view: "template",
            id:"logo",
            template: `<img class="deployed-solution-icon" src="static/img/${this.logo}">`,
            css: 'deployed-solution-logo-view',
            align: "center",
            borderless: true,
            height: 150
        }

        const view = {
            localId: "solutionMenu",
            view: "dataview",
            id: "solutionlist",
            data: this.data,
            width: 930,
            select: 1,
            css: "solutions-list",
            type: {
                width: 300,
                height: 100,
                template: "<div class='overall'><div class='title'>#_name#</div><div class='ip'>#_ip# </div> </div>"
            }
        }

        return {
            type: "space",
            rows:
                [
                    logo,
                    {
                        cols: [{}, {
                            view: "button",
                            id: "btnAddNew",
                            value: "Create New",
                            width: 170,
                            height: 70,
                            css: "webix_primary btnCreateNew",
                            click: function () {
                                this.$scope.show(this.$scope.chat)
                            }
                        }, {}]
                    },
                    migrationView,
                    { cols: [{}, view, {}] }
                ]
        };
    }

    init(view) {
        let self = this;
        self.solutionlist = $$("solutionlist");
        self.migrateView = $$("migrateView");
        self.migrateView.hide();
        self.maxTitleLength = 20;
        solutions.hasMigrated().then(data => {
            const result = data.result;
            if (!result) {
                self.solutionlist.hide()
                $$("logo").hide()
                $$("btnAddNew").hide()

                self.migrateView.show()
                return;
            }
        });
        webix.extend(self.solutionlist, webix.ProgressBar);
        self.solutionlist.showProgress({
            type: "icon",
            hide: false
        });
        self.SolutionDetailsView = self.ui(SolutionDetailsView)

        self.solutionlist.addCss(self.solutionlist.getFirstId(), 'createnewdiv')
        self.solutionlist.attachEvent("onItemClick", function (id) {
            let ret = self.parseData.find(solution => solution.id == id)
            let filtered = Object.assign({}, ret);
            let wids = filtered.wids;
            delete filtered['wids']
            delete filtered['id'];
            // remove keys start with _
            for (let i = 0; i < Object.keys(filtered).length; i++) {
                const key = Object.keys(filtered)[i];
                if (key[0] === '_') {
                    delete filtered[key];
                    i--;
                }
            }
            self.SolutionDetailsView.showInfo(filtered, wids)
        });
    }
}

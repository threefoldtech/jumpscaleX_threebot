
import { BaseView } from './baseview'
import { solutions } from '../../services/deployedSolutions'

const CHAT = "solutions.chatflow?author=tfgrid_solutions&package=tfgrid_solutions&chat=monitoring_solution_deploy"

export default class DeployedMonitoringView extends BaseView {
    constructor(app, name) {

        super(app, name, CHAT, "monitoring_graph.png");
    }

    init(view) {
        super.init(view)
        let self = this
        self.parseData = []
        solutions.listSolution('monitoring').then((data) => {
            const solutions = data.json().solutions
            for (let i = 0; i < solutions.length; i++) {
                let solution = solutions[i];
                solution._type = 'monitoring'
                solution._ip = solution.ip
                solution._name = solution.name.length > self.maxTitleLength ?
                    solution.name.substring(0, self.maxTitleLength) + '...' : solution.name
                self.parseData.push(solution)
            }
            self.solutionlist.parse(self.parseData);
            self.solutionlist.showProgress({ hide: true });
        });
    }
}

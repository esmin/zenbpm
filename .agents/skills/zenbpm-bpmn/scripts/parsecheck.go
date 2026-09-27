// Command parsecheck parses BPMN and DMN files with the ZenBPM model packages.
// The command prints a summary. Use it to confirm that a model is deployable.
// You do not need to run the whole engine.
//
// The program must stay in the ZenBPM module. The program imports the model
// packages. Run these commands from the repository root:
//
//	mkdir -p .tmp-parsecheck
//	cp .agents/skills/zenbpm-bpmn/scripts/parsecheck.go .tmp-parsecheck/main.go
//	go run ./.tmp-parsecheck examples/foo.bpmn examples/bar.dmn
//	rm -rf .tmp-parsecheck
//
// For BPMN, the value `unknown=0` means that the parser found no unsupported
// element. The count includes the elements inside every sub-process.
package main

import (
	"encoding/xml"
	"fmt"
	"os"
	"strings"

	"github.com/pbinitiative/zenbpm/pkg/bpmn/model/bpmn20"
	"github.com/pbinitiative/zenbpm/pkg/dmn/model/dmn"
)

// dmnModelNS is the XML namespace of the DMN 1.3 model.
const dmnModelNS = "https://www.omg.org/spec/DMN/20191111/MODEL/"

func main() {
	for _, path := range os.Args[1:] {
		data, err := os.ReadFile(path)
		if err != nil {
			panic(err)
		}
		fmt.Printf("== %s ==\n", path)
		if strings.HasSuffix(path, ".dmn") {
			checkDMN(data)
			continue
		}
		checkBPMN(data)
	}
}

// checkDMN rejects a document whose root is not a DMN definitions element.
func checkDMN(data []byte) {
	var doc struct {
		XMLName xml.Name
		dmn.TDefinitions
	}
	if err := xml.Unmarshal(data, &doc); err != nil {
		panic(err)
	}
	if doc.XMLName.Local != "definitions" || doc.XMLName.Space != dmnModelNS {
		fmt.Printf("ERROR: the DMN root is {%s}%s, not definitions in %s\n",
			doc.XMLName.Space, doc.XMLName.Local, dmnModelNS)
		os.Exit(1)
	}
	def := doc.TDefinitions
	fmt.Printf("definitions id=%s decisions=%d\n", def.Id, len(def.Decisions))
	for _, d := range def.Decisions {
		if d.DecisionTable == nil {
			fmt.Printf("  decision %s (no table)\n", d.Id)
			continue
		}
		var outs []string
		for _, o := range d.DecisionTable.Outputs {
			outs = append(outs, o.Name)
		}
		fmt.Printf("  decision %s hitPolicy=%s inputs=%d outputs=%v rules=%d\n",
			d.Id, d.DecisionTable.HitPolicy, len(d.DecisionTable.Inputs), outs, len(d.DecisionTable.Rules))
	}
}

func checkBPMN(data []byte) {
	var def bpmn20.TDefinitions
	if err := xml.Unmarshal(data, &def); err != nil {
		panic(err)
	}
	p := def.Process
	fmt.Printf("process=%s services=%d user=%d send=%d receive=%d rule=%d call=%d sub=%d bnd=%d excl=%d par=%d incl=%d unknown=%d\n",
		p.GetId(), len(p.ServiceTasks), len(p.UserTasks), len(p.SendTask), len(p.ReceiveTask),
		len(p.BusinessRuleTask), len(p.CallActivity), len(p.SubProcess), len(p.BoundaryEvent),
		len(p.ExclusiveGateway), len(p.ParallelGateway), len(p.InclusiveGateway), unknownCount(&p))
	for i := range p.SubProcess {
		sp := &p.SubProcess[i]
		fmt.Printf("  sub %s triggeredByEvent=%v\n", sp.GetId(), sp.TriggeredByEvent)
	}
}

// unknownCount counts the unsupported child elements in a process and in every
// sub-process. The function looks at each sub-process again.
func unknownCount(p *bpmn20.TProcess) int {
	n := len(p.UnknownElements)
	for i := range p.SubProcess {
		n += unknownCount(&p.SubProcess[i].TProcess)
	}
	return n
}

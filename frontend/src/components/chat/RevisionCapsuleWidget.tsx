import { useState } from "react";
import { BookOpen, ChevronDown, ChevronUp, Lightbulb, AlertTriangle, CheckCircle, Play, BookMarked } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

interface Topic {
  name: string;
  priority: "high" | "medium" | "low";
  concepts: string[];
  formulas?: string[];
  commonMistakes?: string[];
}

interface RevisionCapsuleWidgetProps {
  subject?: string;
  topics?: Topic[];
}

const mockCapsuleData: Record<string, Topic[]> = {
  physics: [
    {
      name: "Electromagnetic Induction",
      priority: "high",
      concepts: [
        "Faraday's Law: EMF = -dΦ/dt",
        "Lenz's Law determines direction of induced current",
        "Self-inductance L = Φ/I",
      ],
      formulas: ["EMF = -N(dΦ/dt)", "L = μ₀n²Al", "Energy = ½LI²"],
      commonMistakes: [
        "Forgetting negative sign in Faraday's law",
        "Confusing mutual and self-inductance",
      ],
    },
    {
      name: "Thermodynamics",
      priority: "medium",
      concepts: [
        "First Law: ΔU = Q - W",
        "Isothermal: T constant, PV = constant",
        "Adiabatic: Q = 0, PV^γ = constant",
      ],
      formulas: ["W = nRT ln(V₂/V₁)", "Cp - Cv = R", "γ = Cp/Cv"],
    },
  ],
  chemistry: [
    {
      name: "Coordination Compounds",
      priority: "high",
      concepts: [
        "Crystal Field Theory explains color and magnetism",
        "CFSE determines stability",
        "Spectrochemical series: I⁻ < Br⁻ < Cl⁻ < F⁻ < OH⁻ < H₂O < NH₃ < en < NO₂⁻ < CN⁻ < CO",
      ],
      commonMistakes: [
        "Wrong oxidation state calculation",
        "Confusing geometries for d⁸ complexes",
      ],
    },
  ],
  mathematics: [
    {
      name: "Integration Techniques",
      priority: "high",
      concepts: [
        "Integration by parts: ∫udv = uv - ∫vdu",
        "ILATE rule for choosing u",
        "Partial fractions for rational functions",
      ],
      formulas: ["∫eˣ[f(x) + f'(x)]dx = eˣf(x) + C", "∫tan(x)dx = ln|sec(x)| + C"],
    },
  ],
};

export function RevisionCapsuleWidget({ subject = "physics" }: RevisionCapsuleWidgetProps) {
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);
  const topics = mockCapsuleData[subject.toLowerCase()] || mockCapsuleData.physics;

  const getPriorityBadge = (priority: Topic["priority"]) => {
    const styles = {
      high: "bg-red-500/10 text-red-400 border-red-500/20",
      medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
      low: "bg-green-500/10 text-green-400 border-green-500/20",
    };
    return styles[priority];
  };

  const getPriorityLabel = (priority: Topic["priority"]) => {
    const labels = {
      high: "Review Now",
      medium: "Review Soon",
      low: "Good Shape",
    };
    return labels[priority];
  };

  return (
    <Card className="my-3">
      <CardHeader className="pb-3">
        <CardTitle className="text-base sm:text-lg flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-primary/10">
            <BookMarked className="h-4 w-4 text-primary" />
          </div>
          <span>Revision Capsule: <span className="capitalize">{subject}</span></span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {topics.map((topic, index) => (
          <Card key={topic.name} className="overflow-hidden">
            {/* Topic Header */}
            <button
              onClick={() => setExpandedTopic(expandedTopic === topic.name ? null : topic.name)}
              className="w-full flex items-center justify-between p-3 sm:p-4 hover:bg-secondary/30 transition-colors"
            >
              <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
                <Badge 
                  variant="outline"
                  className={cn(
                    "text-xs whitespace-nowrap shrink-0",
                    getPriorityBadge(topic.priority)
                  )}
                >
                  {getPriorityLabel(topic.priority)}
                </Badge>
                <span className="font-medium text-foreground text-sm sm:text-base truncate">{topic.name}</span>
              </div>
              {expandedTopic === topic.name ? (
                <ChevronUp className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground shrink-0 ml-2" />
              ) : (
                <ChevronDown className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground shrink-0 ml-2" />
              )}
            </button>

            {/* Expanded Content */}
            {expandedTopic === topic.name && (
              <>
                <Separator />
                <CardContent className="p-3 sm:p-4 space-y-4">
                  {/* Key Concepts */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="h-4 w-4 text-primary" />
                      <h4 className="text-sm font-semibold text-foreground">Key Concepts</h4>
                    </div>
                    <ul className="space-y-2 pl-6">
                      {topic.concepts.map((concept, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                          <span>{concept}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Formulas */}
                  {topic.formulas && topic.formulas.length > 0 && (
                    <>
                      <Separator />
                      <div className="space-y-2">
                        <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
                          <BookOpen className="h-4 w-4 text-primary" />
                          Important Formulas
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {topic.formulas.map((formula, i) => (
                            <Badge
                              key={i}
                              variant="secondary"
                              className="text-xs font-mono py-1.5 px-2.5"
                            >
                              {formula}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </>
                  )}

                  {/* Common Mistakes */}
                  {topic.commonMistakes && topic.commonMistakes.length > 0 && (
                    <>
                      <Separator />
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          <h4 className="text-sm font-semibold text-foreground">Common Mistakes</h4>
                        </div>
                        <ul className="space-y-2 pl-6">
                          {topic.commonMistakes.map((mistake, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <span className="text-red-500 font-bold mt-0.5">•</span>
                              <span>{mistake}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </>
                  )}

                  {/* Practice Button */}
                  <Separator />
                  <Button size="sm" className="w-full gap-2">
                    <Play className="h-4 w-4" />
                    Practice This Topic
                  </Button>
                </CardContent>
              </>
            )}
          </Card>
        ))}
      </CardContent>
    </Card>
  );
}

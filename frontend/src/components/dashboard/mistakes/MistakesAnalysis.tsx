import { useState } from 'react';
import { MistakesChart } from './MistakesChart';
import { ChapterMistakesTable } from './ChapterMistakesTable';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Atom, FlaskConical, Calculator, PlayCircle, ChevronRight } from "lucide-react";
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

const MOCK_CHART_DATA = [
    { chapter: 'Alternating Current', incorrect: 3, correct: 3, unattempted: 24 },
    { chapter: 'Semiconductors', incorrect: 5, correct: 15, unattempted: 2 },
    { chapter: 'Ray Optics', incorrect: 8, correct: 12, unattempted: 5 },
    { chapter: 'Wave Optics', incorrect: 2, correct: 8, unattempted: 10 },
    { chapter: 'Electric Charges', incorrect: 6, correct: 10, unattempted: 4 },
];

const MOCK_TABLE_DATA = [
    {
        id: '1',
        name: 'Alternating Current',
        attemptedWrong: 3,
        notAttempted: 24,
        attemptedCorrect: 3,
        totalQuestions: 30
    },
    {
        id: '2',
        name: 'Semiconductors',
        attemptedWrong: 5,
        notAttempted: 2,
        attemptedCorrect: 15,
        totalQuestions: 22
    },
    {
        id: '3',
        name: 'Ray Optics',
        attemptedWrong: 8,
        notAttempted: 5,
        attemptedCorrect: 12,
        totalQuestions: 25
    },
];

export const MistakesAnalysis = () => {
    const [subject, setSubject] = useState('physics');

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                {/* Subject Tabs */}
                <Tabs defaultValue="physics" className="w-full sm:w-auto" onValueChange={setSubject}>
                    <TabsList className="grid w-full grid-cols-3 h-11 p-1 bg-transparent border-b rounded-none w-auto gap-4">
                        <TabsTrigger
                            value="physics"
                            className="rounded-none border-b-2 border-transparent data-[state=active]:border-emerald-500 data-[state=active]:text-emerald-500 data-[state=active]:shadow-none px-4 py-2 h-full flex items-center gap-2"
                        >
                            <Atom className="h-4 w-4" />
                            Physics
                        </TabsTrigger>
                        <TabsTrigger
                            value="chemistry"
                            className="rounded-none border-b-2 border-transparent data-[state=active]:border-orange-500 data-[state=active]:text-orange-500 data-[state=active]:shadow-none px-4 py-2 h-full flex items-center gap-2"
                        >
                            <FlaskConical className="h-4 w-4" />
                            Chemistry
                        </TabsTrigger>
                        <TabsTrigger
                            value="maths"
                            className="rounded-none border-b-2 border-transparent data-[state=active]:border-blue-500 data-[state=active]:text-blue-500 data-[state=active]:shadow-none px-4 py-2 h-full flex items-center gap-2"
                        >
                            <Calculator className="h-4 w-4" />
                            Mathematics
                        </TabsTrigger>
                    </TabsList>
                </Tabs>
            </div>

            <div className="flex bg-background p-2 rounded-lg border items-center gap-4 flex-wrap">
                <Select defaultValue="all-tests">
                    <SelectTrigger className="w-[180px] border-none shadow-none bg-transparent hover:bg-muted/50 text-blue-600 font-medium h-9">
                        <div className="flex items-center gap-1">
                            <span className="text-muted-foreground font-normal">Test Type :</span>
                            <SelectValue placeholder="All Tests" />
                        </div>
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all-tests">All Tests</SelectItem>
                        <SelectItem value="mock-tests">Mock Tests</SelectItem>
                        <SelectItem value="practice-tests">Practice Tests</SelectItem>
                    </SelectContent>
                </Select>

                <div className="h-6 w-px bg-border hidden sm:block" />

                <div className="flex items-center gap-2 flex-wrap">
                    <Button variant="default" size="sm" className="h-8 rounded-full bg-blue-600 hover:bg-blue-700 text-white gap-2 px-4">
                        All
                        <ChevronRight className="h-3 w-3 rotate-90" />
                    </Button>
                    <Button variant="outline" size="sm" className="h-8 rounded-full border-muted-foreground/30 text-muted-foreground hover:text-foreground hover:border-foreground">
                        Last 3 Tests
                    </Button>
                    <Button variant="outline" size="sm" className="h-8 rounded-full border-muted-foreground/30 text-muted-foreground hover:text-foreground hover:border-foreground">
                        Last 5 Tests
                    </Button>
                    <Button variant="outline" size="sm" className="h-8 rounded-full border-muted-foreground/30 text-muted-foreground hover:text-foreground hover:border-foreground">
                        Attempted in last 30 days
                    </Button>
                </div>
            </div>

            <MistakesChart data={MOCK_CHART_DATA} />

            <ChapterMistakesTable data={MOCK_TABLE_DATA} />

        </div>
    );
};



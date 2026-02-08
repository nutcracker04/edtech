import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    ArrowUpDown,
    TrendingUp,
    TrendingDown,
    Minus,
    ChevronRight
} from "lucide-react";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

// ... imports
interface ChapterData {
    id: string;
    name: string;
    attemptedWrong: number;
    notAttempted: number;
    attemptedCorrect: number;
    totalQuestions: number;
}

interface ChapterMistakesTableProps {
    data: ChapterData[];
}

export const ChapterMistakesTable = ({ data }: ChapterMistakesTableProps) => {
    return (
        <Card className="w-full">
            <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-bold">Chapter-wise Mistakes</CardTitle>
                </div>
            </CardHeader>
            <CardContent>
                <div className="rounded-md border max-h-[400px] overflow-y-auto">
                    <Table>
                        <TableHeader className="sticky top-0 bg-background z-10 shadow-sm">
                            <TableRow className="bg-muted/50">
                                <TableHead className="w-[300px] font-semibold">Chapter Name</TableHead>
                                <TableHead className="text-center font-semibold text-red-500">Attempted<br />Wrong</TableHead>
                                <TableHead className="text-center font-semibold text-muted-foreground">Not<br />Attempted</TableHead>
                                <TableHead className="text-center font-semibold text-emerald-500">Attempted<br />Correct</TableHead>
                                <TableHead className="text-center font-semibold">Total<br />Questions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {data.map((chapter) => (
                                <TableRow key={chapter.id} className="hover:bg-muted/5">
                                    <TableCell className="font-medium">
                                        <div className="flex items-center gap-2 group cursor-pointer">
                                            <TrendingUp className="h-4 w-4 text-blue-500" />
                                            <span className="group-hover:text-primary transition-colors">{chapter.name}</span>
                                            <ChevronRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground ml-auto" />
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-center font-bold text-red-500">
                                        {chapter.attemptedWrong}
                                    </TableCell>
                                    <TableCell className="text-center font-bold text-muted-foreground">
                                        {chapter.notAttempted}
                                    </TableCell>
                                    <TableCell className="text-center font-bold text-emerald-500">
                                        {chapter.attemptedCorrect}
                                    </TableCell>
                                    <TableCell className="text-center font-bold text-foreground">
                                        {chapter.totalQuestions}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            </CardContent>
        </Card>
    );
};

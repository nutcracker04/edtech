import { MainLayout } from "@/components/layout/MainLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Database, FileUp, Tag, ListTree, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

const AdminDashboard = () => {
    const navigate = useNavigate();

    const adminActions = [
        {
            title: "Hierarchy Manager",
            description: "Manage Subjects, Chapters, and Topics.",
            icon: ListTree,
            path: "/admin/hierarchy",
            color: "text-blue-500",
            bgColor: "bg-blue-500/10",
        },
        {
            title: "Concept Graph",
            description: "Extract concepts from NCERT textbooks and build knowledge graph.",
            icon: Database,
            path: "/admin/concept-graph",
            color: "text-purple-500",
            bgColor: "bg-purple-500/10",
        },
        {
            title: "Upload & Tag",
            description: "Upload papers or manually tag extracted questions.",
            icon: FileUp,
            path: "/admin/upload",
            color: "text-emerald-500",
            bgColor: "bg-emerald-500/10",
        },
        {
            title: "Repository",
            description: "View and manage the global tagged repository.",
            icon: Database,
            path: "/admin/repository",
            color: "text-orange-500",
            bgColor: "bg-orange-500/10",
        },
    ];

    return (
        <MainLayout>
            <div className="container py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
                    <p className="text-muted-foreground">Manage the Question Repository and Content Hierarchy.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {adminActions.map((action) => (
                        <Card key={action.title} className="hover:shadow-lg transition-shadow border-2 border-border/50">
                            <CardHeader className="flex flex-row items-center gap-4">
                                <div className={`${action.bgColor} ${action.color} p-3 rounded-xl`}>
                                    <action.icon className="h-6 w-6" />
                                </div>
                                <div>
                                    <CardTitle>{action.title}</CardTitle>
                                    <CardDescription>{action.description}</CardDescription>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <Button
                                    className="w-full justify-between"
                                    onClick={() => navigate(action.path)}
                                >
                                    Manage {action.title}
                                    <ArrowRight className="h-4 w-4 ml-2" />
                                </Button>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </MainLayout>
    );
};

export default AdminDashboard;

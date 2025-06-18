import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  GitPullRequest,
  ExternalLink,
  Clock,
  CheckCircle,
  AlertCircle,
  Send,
  MessageSquare,
  Plus,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import PRPreview from "@/components/PRPreview";

interface FollowUpRequest {
  id: string;
  prompt: string;
  status: "pending" | "processing" | "completed" | "error";
  createdAt: Date;
  pullRequestUrl?: string;
}

interface PullRequest {
  id: string;
  sessionId: string;
  prompt: string;
  status: "pending" | "processing" | "completed" | "error";
  pullRequestUrl?: string;
  prNumber?: number;
  createdAt: Date;
  followUps: FollowUpRequest[];
  isExpanded?: boolean;
}

const Index: React.FC = () => {
  const [prompt, setPrompt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([]);
  const [followUpPrompts, setFollowUpPrompts] = useState<{
    [key: string]: string;
  }>({});
  const [submittingFollowUps, setSubmittingFollowUps] = useState<{
    [key: string]: boolean;
  }>({});
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(
        "http://localhost:8001/translate-and-forward/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({ prompt }),
        }
      );
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API call failed with status ${response.status}: ${errorText}`
        );
      }
      const data = await response.json();
      console.log("API Response data:", data);

      // 1) Extract the full PR URL
      const urlMatch = data.message.match(/https?:\/\/\S+\/pull\/\d+/);
      const pullRequestUrl = urlMatch ? urlMatch[0] : "";

      // 2) Extract session_id if provided
      let sessionId = data.session_id;
      if (!sessionId) {
        const sessMatch = data.message.match(/session_id=([\w-]+)/);
        sessionId = sessMatch ? sessMatch[1] : "";
      }

      // 3) Derive the numeric PR number for preview
      const prNumber = pullRequestUrl
        ? parseInt(pullRequestUrl.split("/").pop() || "0", 10)
        : undefined;

      const newPR: PullRequest = {
        id: Math.random().toString(36).substr(2, 9),
        sessionId,
        prompt,
        status: "pending",
        pullRequestUrl,
        prNumber,
        createdAt: new Date(),
        followUps: [],
        isExpanded: false,
      };

      setPullRequests((prev) => [newPR, ...prev]);
      setPrompt("");
      toast({
        title: "Request submitted!",
        description: "Your pull request is being generated.",
      });

      // If we got a PR URL immediately, mark it completed
      if (pullRequestUrl) {
        updatePRStatus(newPR.id, "completed");
      } else {
        // otherwise simulate a processing flow
        setTimeout(() => updatePRStatus(newPR.id, "processing"), 2000);
        setTimeout(() => {
          const fakeUrl = `http://localhost:8001/preview/${newPR.id}`;
          setPullRequests((prs) =>
            prs.map((pr) =>
              pr.id === newPR.id
                ? { ...pr, status: "completed", pullRequestUrl: fakeUrl }
                : pr
            )
          );
        }, 8000);
      }
    } catch (error: any) {
      console.error("Error in handleSubmit:", error);
      const isNetworkError =
        error instanceof TypeError && error.message.includes("fetch");
      toast({
        title: isNetworkError ? "Connection Error" : "Error",
        description: isNetworkError
          ? "Cannot connect to backend. Check server & CORS."
          : `Failed to submit request: ${error.message}`,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFollowUpSubmit = async (prId: string) => {
    const followUpPrompt = followUpPrompts[prId];
    if (!followUpPrompt?.trim()) return;

    setSubmittingFollowUps((prev) => ({ ...prev, [prId]: true }));
    try {
      const pr = pullRequests.find((p) => p.id === prId);
      if (!pr) return;

      const response = await fetch(
        "http://localhost:8001/translate-and-forward/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            session_id: pr.sessionId,
            prompt: followUpPrompt,
          }),
        }
      );
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();

      const newFollowUp: FollowUpRequest = {
        id: Math.random().toString(36).substr(2, 9),
        prompt: followUpPrompt,
        status: "pending",
        createdAt: new Date(),
        pullRequestUrl: data.pullRequestUrl,
      };

      setPullRequests((prev) =>
        prev.map((p) =>
          p.id === prId
            ? { ...p, followUps: [...p.followUps, newFollowUp] }
            : p
        )
      );
      setFollowUpPrompts((prev) => ({ ...prev, [prId]: "" }));
      toast({
        title: "Follow-up submitted!",
        description: "Your PR adjustment request is being processed.",
      });

      if (data.pullRequestUrl) {
        updateFollowUpStatus(prId, newFollowUp.id, "completed");
      } else {
        setTimeout(
          () => updateFollowUpStatus(prId, newFollowUp.id, "processing"),
          1500
        );
        setTimeout(
          () => updateFollowUpStatus(prId, newFollowUp.id, "completed"),
          6000
        );
      }
    } catch (error: any) {
      console.error("Error in handleFollowUpSubmit:", error);
      const isNetworkError =
        error instanceof TypeError && error.message.includes("fetch");
      toast({
        title: isNetworkError ? "Connection Error" : "Error",
        description: isNetworkError
          ? "Cannot connect to backend. Check server & CORS."
          : `Failed to submit follow-up: ${error.message}`,
        variant: "destructive",
      });
    } finally {
      setSubmittingFollowUps((prev) => ({ ...prev, [prId]: false }));
    }
  };

  const updatePRStatus = (id: string, status: PullRequest["status"]) => {
    setPullRequests((prev) =>
      prev.map((pr) => (pr.id === id ? { ...pr, status } : pr))
    );
  };

  const updateFollowUpStatus = (
    prId: string,
    followUpId: string,
    status: FollowUpRequest["status"]
  ) => {
    setPullRequests((prev) =>
      prev.map((pr) =>
        pr.id === prId
          ? {
              ...pr,
              followUps: pr.followUps.map((fu) =>
                fu.id === followUpId ? { ...fu, status } : fu
              ),
            }
          : pr
      )
    );
  };

  const togglePRExpansion = (prId: string) => {
    setPullRequests((prev) =>
      prev.map((pr) =>
        pr.id === prId ? { ...pr, isExpanded: !pr.isExpanded } : pr
      )
    );
  };

  const getStatusIcon = (
    status: PullRequest["status"] | FollowUpRequest["status"]
  ) => {
    switch (status) {
      case "pending":
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case "processing":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getStatusColor = (
    status: PullRequest["status"] | FollowUpRequest["status"]
  ) => {
    switch (status) {
      case "pending":
        return "bg-yellow-500/20 text-yellow-300 border-yellow-500/30";
      case "processing":
        return "bg-blue-500/20 text-blue-300 border-blue-500/30";
      case "completed":
        return "bg-green-500/20 text-green-300 border-green-500/30";
      case "error":
        return "bg-red-500/20 text-red-300 border-red-500/30";
    }
    return "";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <GitPullRequest className="h-12 w-12 text-blue-400 mr-3" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              AI-Powered Data Engineering
            </h1>
          </div>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Transform your ideas into pull requests and refine them with
            follow-up requests until they're perfect.
          </p>
        </div>

        {/* Submit Form */}
        <Card className="mb-8 bg-slate-800/50 border-slate-700 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <Send className="h-5 w-5 mr-2 text-blue-400" />
              Submit Your Request
            </CardTitle>
            <CardDescription className="text-slate-400">
              Describe the changes you want to make. You can refine your
              request with follow-ups after submission.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Textarea
                placeholder="e.g., Add a login form with email validation and password strength indicator..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="min-h-32 bg-slate-900/50 border-slate-600 text-white placeholder:text-slate-500 font-mono text-sm"
                disabled={isSubmitting}
              />
              <Button
                type="submit"
                disabled={!prompt.trim() || isSubmitting}
                className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-medium px-6"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Generate Pull Request
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Pull Requests List */}
        {pullRequests.length > 0 ? (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
              <GitPullRequest className="h-6 w-6 mr-2 text-blue-400" />
              Your Pull Requests
            </h2>
            {pullRequests.map((pr) => (
              <Card
                key={pr.id}
                className="bg-slate-800/50 border-slate-700 backdrop-blur-sm hover:bg-slate-800/70 transition-all duration-200"
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(pr.status)}
                      <Badge
                        variant="outline"
                        className={getStatusColor(pr.status)}
                      >
                        {pr.status.charAt(0).toUpperCase() +
                          pr.status.slice(1)}
                      </Badge>
                      <span className="text-sm text-slate-400 font-mono">
                        Session: {pr.sessionId}
                      </span>
                      {pr.followUps.length > 0 && (
                        <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30">
                          {pr.followUps.length} follow-up
                          {pr.followUps.length !== 1 ? "s" : ""}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-slate-500">
                        {pr.createdAt.toLocaleTimeString()}
                      </span>
                      {(pr.followUps.length > 0 ||
                        pr.status === "completed") && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => togglePRExpansion(pr.id)}
                          className="text-slate-400 hover:text-white"
                        >
                          <MessageSquare className="h-4 w-4 mr-1" />
                          {pr.isExpanded ? "Collapse" : "Expand"}
                        </Button>
                      )}
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="text-slate-300 font-mono text-sm bg-slate-900/50 p-3 rounded border border-slate-700">
                      {pr.prompt}
                    </p>
                  </div>

                  {pr.pullRequestUrl && pr.status === "completed" && (
                    <div className="flex items-center justify-between bg-slate-900/50 p-3 rounded border border-slate-700 mb-4">
                      <span className="text-sm text-slate-300">
                        Pull Request Ready
                      </span>
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          asChild
                          className="border-blue-500/50 text-blue-300 hover:bg-blue-500/10"
                        >
                          <a
                            href={pr.pullRequestUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <ExternalLink className="h-4 w-4 mr-2" />
                            View PR
                          </a>
                        </Button>
                        {pr.prNumber != null && (
                          <PRPreview
                            requestId={pr.prNumber.toString()}
                          />
                        )}
                      </div>
                    </div>
                  )}

                  {pr.status === "processing" && (
                    <div className="bg-slate-900/50 p-3 rounded border border-slate-700 mb-4">
                      <div className="flex items-center space-x-2 text-sm text-slate-400">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>
                          Analyzing prompt and generating code changes...
                        </span>
                      </div>
                      <div className="mt-2 w-full bg-slate-700 rounded-full h-2">
                        <div
                          className="h-2 rounded-full animate-pulse"
                          style={{ width: "60%" }}
                        />
                      </div>
                    </div>
                  )}

                  {pr.status === "completed" && (
                    <div className="space-y-4">
                      {/* Follow-up Input */}
                      <div className="bg-slate-900/30 p-4 rounded border border-slate-600 border-dashed">
                        <div className="flex items-center mb-3">
                          <Plus className="h-4 w-4 text-green-400 mr-2" />
                          <span className="text-sm font-medium text-slate-300">
                            Request Adjustments
                          </span>
                        </div>
                        <div className="space-y-3">
                          <Textarea
                            placeholder="e.g., Make the button larger, change the color scheme, add validation..."
                            value={followUpPrompts[pr.id] || ""}
                            onChange={(e) =>
                              setFollowUpPrompts((prev) => ({
                                ...prev,
                                [pr.id]: e.target.value,
                              }))
                            }
                            className="min-h-20 bg-slate-800/50 border-slate-600 text-white placeholder:text-slate-500 font-mono text-sm"
                            disabled={submittingFollowUps[pr.id]}
                          />
                          <Button
                            onClick={() => handleFollowUpSubmit(pr.id)}
                            disabled={
                              !followUpPrompts[pr.id]?.trim() ||
                              submittingFollowUps[pr.id]
                            }
                            size="sm"
                            className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
                          >
                            {submittingFollowUps[pr.id] ? (
                              <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Submitting...
                              </>
                            ) : (
                              <>
                                <Send className="h-4 w-4 mr-2" />
                                Submit Adjustment
                              </>
                            )}
                          </Button>
                        </div>
                      </div>

                      {/* Follow-ups List */}
                      {pr.isExpanded && pr.followUps.length > 0 && (
                        <div className="space-y-3">
                          <h4 className="text-sm font-medium text-slate-300 flex items-center">
                            <MessageSquare className="h-4 w-4 mr-2 text-purple-400" />
                            Follow-up Requests
                          </h4>
                          {pr.followUps.map((followUp, index) => (
                            <div
                              key={followUp.id}
                              className="bg-slate-900/40 p-3 rounded border border-slate-600"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center space-x-2">
                                  {getStatusIcon(followUp.status)}
                                  <Badge
                                    variant="outline"
                                    className={getStatusColor(followUp.status)}
                                  >
                                    {followUp.status
                                      .charAt(0)
                                      .toUpperCase() +
                                      followUp.status.slice(1)}
                                  </Badge>
                                  <span className="text-xs text-slate-500">
                                    Follow-up #{index + 1}
                                  </span>
                                </div>
                                <span className="text-xs text-slate-500">
                                  {followUp.createdAt.toLocaleTimeString()}
                                </span>
                              </div>
                              <p className="text-slate-400 text-sm font-mono bg-slate-800/50 p-2 rounded">
                                {followUp.prompt}
                              </p>
                              {followUp.pullRequestUrl &&
                                followUp.status === "completed" && (
                                  <div className="mt-2">
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      asChild
                                      className="border-green-500/50 text-green-300 hover:bg-green-500/10"
                                    >
                                      <a
                                        href={followUp.pullRequestUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                      >
                                        <ExternalLink className="h-4 w-4 mr-2" />
                                        View Updated PR
                                      </a>
                                    </Button>
                                  </div>
                                )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-slate-800/30 border-slate-700 border-dashed">
            <CardContent className="p-12 text-center">
              <GitPullRequest className="h-16 w-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-400 mb-2">
                No pull requests yet
              </h3>
              <p className="text-slate-500">
                Submit your first prompt above to get started!
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};
export default Index;
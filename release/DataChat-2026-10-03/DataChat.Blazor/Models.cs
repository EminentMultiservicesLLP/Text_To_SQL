using System.Text.Json;

namespace DataChat.Blazor;

public sealed record ChatRequest(
    string ClientId,
    string UserId,
    string ConversationId,
    string Message,
    Dictionary<string, string> Overrides,
    JsonElement? Plan = null);

public sealed record ColumnInfo(string Name, string Label, string Kind, string? Format);

public sealed record ChartInfo(string Type, string X, List<string> Y);

public sealed record ClarifyOption(string Label, Dictionary<string, string> Overrides);

/// <summary>A next question offered under an answer; sending its plan back runs it without the model.</summary>
public sealed record FollowUp(string Label, JsonElement Plan);

public sealed record ChatResponse
{
    /// <summary>answer | clarify | unsupported | error | greeting</summary>
    public string Type { get; init; } = "error";
    public string Text { get; init; } = "";
    public List<string> Assumptions { get; init; } = [];
    public string? Sql { get; init; }
    public List<ColumnInfo> Columns { get; init; } = [];
    public List<List<JsonElement>> Rows { get; init; } = [];
    public int RowCount { get; init; }
    public bool Capped { get; init; }
    public ChartInfo? Chart { get; init; }
    public List<ClarifyOption> Options { get; init; } = [];
    public List<FollowUp> FollowUps { get; init; } = [];
    public long? QueryId { get; init; }
    public string? Source { get; init; }
    public int ElapsedMs { get; init; }
}

public sealed record FeedbackRequest(string ClientId, string UserId, long QueryId, int Rating, string? Comment);

public sealed record ClientInfo(
    string ClientId,
    string DisplayName,
    List<string> Examples,
    string CurrencySymbol,
    bool IndianGrouping);

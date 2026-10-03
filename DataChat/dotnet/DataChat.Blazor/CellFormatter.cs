using System.Globalization;
using System.Text.Json;

namespace DataChat.Blazor;

/// <summary>Formats result cells the same way the engine formats numbers in its answer text.</summary>
public sealed class CellFormatter
{
    private readonly string _currency;
    private readonly bool _indian;
    private readonly NumberFormatInfo _nf;

    public CellFormatter(string currencySymbol, bool indianGrouping)
    {
        _currency = currencySymbol;
        _indian = indianGrouping;
        _nf = (NumberFormatInfo)CultureInfo.InvariantCulture.NumberFormat.Clone();
        _nf.NumberGroupSizes = indianGrouping ? [3, 2] : [3];
    }

    public static double? AsNumber(JsonElement v) =>
        v.ValueKind == JsonValueKind.Number && v.TryGetDouble(out var d) ? d : null;

    public static string AsText(JsonElement v) => v.ValueKind switch
    {
        JsonValueKind.String => v.GetString() ?? "",
        JsonValueKind.Null or JsonValueKind.Undefined => "",
        _ => v.GetRawText(),
    };

    public string Format(JsonElement v, string? format) =>
        AsNumber(v) is { } d ? FormatNumber(d, format) : AsText(v);

    public string FormatNumber(double d, string? format) => format switch
    {
        "currency" => Math.Abs(d) >= 100 ? _currency + Math.Round(d).ToString("N0", _nf) : _currency + d.ToString("N2", _nf),
        "integer" => Math.Round(d).ToString("N0", _nf),
        "percent" => d.ToString("0.0", _nf) + "%",
        _ => d % 1 == 0 ? d.ToString("N0", _nf) : d.ToString("N2", _nf),
    };

    /// <summary>Short axis labels: 12.5L / 1.2Cr with Indian grouping, otherwise 12.5K / 1.2M.</summary>
    public string Compact(double d)
    {
        var a = Math.Abs(d);
        string s = _indian
            ? a >= 1e7 ? $"{d / 1e7:0.#}Cr" : a >= 1e5 ? $"{d / 1e5:0.#}L" : a >= 1e3 ? $"{d / 1e3:0.#}K" : $"{d:0.#}"
            : a >= 1e9 ? $"{d / 1e9:0.#}B" : a >= 1e6 ? $"{d / 1e6:0.#}M" : a >= 1e3 ? $"{d / 1e3:0.#}K" : $"{d:0.#}";
        return s;
    }
}

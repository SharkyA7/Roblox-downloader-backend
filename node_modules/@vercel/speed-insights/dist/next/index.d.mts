interface SpeedInsightsProps {
    dsn?: string;
    sampleRate?: number;
    route?: string | null;
    beforeSend?: BeforeSend;
    debug?: boolean;
    scriptSrc?: string;
    endpoint?: string;
}
type EventTypes = 'vital';
interface BeforeSendEvent {
    type: EventTypes;
    url: string;
    route?: string;
}
type BeforeSend = (event: BeforeSendEvent) => BeforeSendEvent | null | undefined | false;
interface Functions {
    beforeSend?: BeforeSend;
}
interface SpeedInsights$1<T extends keyof Functions = keyof Functions> {
    queue: [T, Functions[T]][];
    addAction: (action: T, data: Functions[T]) => void;
}
declare global {
    interface Window {
        /** Base interface to track events */
        si?: SpeedInsights$1['addAction'];
        /** Queue for speed insights datapoints, before the library is loaded */
        siq?: SpeedInsights$1['queue'];
        sil?: boolean;
        /** used by Astro component only */
        speedInsightsBeforeSend?: BeforeSend;
    }
}

type Props = Omit<SpeedInsightsProps, 'route'>;
declare function SpeedInsights(props: Props): null;

export { SpeedInsights };
